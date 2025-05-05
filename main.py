import requests
import ctypes
import time
from pathlib import Path
from PIL import Image


def get_new_wallpaper_url():
    api_url = "http://sp1.rock.hosts.name:34633/images"
    response = requests.get(api_url)
    if response.ok:
        return response.json()["url"]
    else:
        raise Exception("Ошибка картиночки")


def download_image(url, save_path):
    img_data = requests.get(url).content
    with open(save_path, 'wb') as handler:
        handler.write(img_data)
    print(f"Картинка скачана: {save_path}")


def convert_to_bmp_with_padding(src_path):
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    screen_size = (screen_width, screen_height)

    with Image.open(src_path) as img:
        img = img.convert("RGB")

        ratio_w = screen_width / img.width
        ratio_h = screen_height / img.height

        scale_ratio = min(ratio_w, ratio_h)

        new_width = int(img.width * scale_ratio)
        new_height = int(img.height * scale_ratio)

        img = img.resize((new_width, new_height), Image.LANCZOS)

        new_img = Image.new("RGB", screen_size, (0, 0, 0))
        offset = ((screen_width - new_width) // 2, (screen_height - new_height) // 2)
        new_img.paste(img, offset)

        dst_path = src_path.with_suffix(".bmp")
        new_img.save(dst_path, "BMP")
        print(f"Конвертировано с вписыванием в экран: {dst_path}")
        return dst_path


def set_wallpaper(image_path):
    abs_path = str(image_path.resolve())
    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
    if result:
        print(f"Обои установлены: {abs_path}")
    else:
        print("не удалось установить обои")


def cleanup_old_wallpapers(wallpapers_dir: Path, keep_file: Path):
    for file in wallpapers_dir.iterdir():
        if file != keep_file and file.is_file():
            try:
                file.unlink()
                print(f"Удалён старый файл: {file.name}")
            except Exception as e:
                print(f"Не удалось удалить {file.name}: {e}")


def main_loop(interval_seconds=300):
    wallpapers_dir = Path("wallpapers")
    wallpapers_dir.mkdir(exist_ok=True)

    current_bmp = None

    while True:
        try:
            img_url = get_new_wallpaper_url()
            file_name = img_url.split("/")[-1]
            save_path = wallpapers_dir / file_name

            if current_bmp:
                cleanup_old_wallpapers(wallpapers_dir, current_bmp)

            download_image(img_url, save_path)
            bmp_path = convert_to_bmp_with_padding(save_path)
            set_wallpaper(bmp_path)

            current_bmp = bmp_path
        except Exception as e:
            print(f"Ошибка: {e}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main_loop(interval_seconds=10)
