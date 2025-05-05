import requests
import time
import subprocess
from pathlib import Path
from PIL import Image
import os


def get_new_wallpaper_url():
    api_url = "http://sp1.rock.hosts.name:34633/images"
    response = requests.get(api_url)
    if response.ok:
        return response.json()["url"]
    else:
        raise Exception("Ошибка при получении URL изображения")


def download_image(url, save_path):
    img_data = requests.get(url).content
    with open(save_path, 'wb') as handler:
        handler.write(img_data)
    print(f"Изображение сохранено: {save_path}")


def resize_image(src_path):
    try:
        output = subprocess.check_output(["xrandr"]).decode()
        for line in output.splitlines():
            if '*' in line:
                parts = line.split()
                width = int(parts[parts.index('current') + 1])
                height = int(parts[parts.index('current') + 3].replace(',', ''))
                break
        else:
            width, height = 1920, 1080  # значения по умолчанию
    except:
        width, height = 1920, 1080
    
    screen_size = (width, height)

    with Image.open(src_path) as img:
        img = img.convert("RGB")

        ratio_w = width / img.width
        ratio_h = height / img.height
        scale_ratio = min(ratio_w, ratio_h)

        new_width = int(img.width * scale_ratio)
        new_height = int(img.height * scale_ratio)

        img = img.resize((new_width, new_height), Image.LANCZOS)

        # Центрируем картинку
        new_img = Image.new("RGB", screen_size, (0, 0, 0))
        offset = ((width - new_width) // 2, (height - new_height) // 2)
        new_img.paste(img, offset)

        dst_path = src_path.with_suffix(".jpg")
        new_img.save(dst_path, "JPEG", quality=95)
        print(f"Изображение адаптировано под экран: {dst_path}")
        return dst_path


def set_kde_wallpaper(image_path):
    abs_path = str(image_path.resolve())
    
    set_cmd = f"""
    qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
    var allDesktops = desktops();
    for (i=0;i<allDesktops.length;i++) {{
        d = allDesktops[i];
        d.wallpaperPlugin = "org.kde.image";
        d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
        d.writeConfig("Image", "file://{abs_path}");
        d.writeConfig("FillMode", "2");  // 0=растянуть, 1=заполнить, 2=вписать
    }}'
    """
    
    try:
        subprocess.run("qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var allDesktops = desktops();for (i=0;i<allDesktops.length;i++) {d = allDesktops[i];d.currentConfigGroup = Array(\"Wallpaper\", \"org.kde.image\", \"General\");d.writeConfig(\"Image\", \"\")}'", 
                      shell=True, check=False)
        
        subprocess.run(set_cmd, shell=True, check=True)
        print(f"Обои успешно установлены: {abs_path}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке обоев: {e}")
        raise Exception("Не удалось установить обои")


def cleanup_old_wallpapers(wallpapers_dir: Path, keep_file: Path):
    for file in wallpapers_dir.iterdir():
        if file != keep_file and file.is_file():
            try:
                file.unlink()
                print(f"Удален старый файл: {file.name}")
            except Exception as e:
                print(f"Не удалось удалить {file.name}: {e}")


def main_loop(interval_seconds=300):
    wallpapers_dir = Path.home() / ".local" / "share" / "wallpapers"
    wallpapers_dir.mkdir(exist_ok=True, parents=True)

    current_wallpaper = None

    while True:
        try:
            img_url = get_new_wallpaper_url()
            file_name = img_url.split("/")[-1]
            save_path = wallpapers_dir / file_name


            if current_wallpaper:
                cleanup_old_wallpapers(wallpapers_dir, current_wallpaper)

            download_image(img_url, save_path)
            wallpaper_path = resize_image(save_path)
            set_kde_wallpaper(wallpaper_path)

            current_wallpaper = wallpaper_path
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        
        print(f"Ожидание {interval_seconds} секунд до следующего обновления...")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    try:
        print("Запуск автоматической смены обоев для KDE Plasma")
        print("Для остановки нажмите Ctrl+C")
        main_loop(interval_seconds=10)
    except KeyboardInterrupt:
        print("\nРабота программы завершена")
