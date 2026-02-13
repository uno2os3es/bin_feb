#!/data/data/com.termux/files/usr/bin/env python3
import glob

from PIL import Image


def reduce_image_size(image_path, scale_factor=0.75) -> None:
    """Reduce image size by the given scale factor and overwrite the original file."""
    try:
        with Image.open(image_path) as img:
            # Calculate new dimensions
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)

            # Resize image using LANCZOS filter for good quality
            resized_img = img.resize(
                (new_width, new_height),
                Image.LANCZOS,
            )

            # Save over original file, preserving format and optimizing
            resized_img.save(
                image_path,
                optimize=True,
                quality=85,
            )

            print(f"Reduced: {image_path} ({img.width}x{img.height} -> {new_width}x{new_height})")

    except Exception as e:
        print(f"Error processing {image_path}: {e!s}")


def main() -> None:
    # Supported image formats
    image_extensions = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.bmp",
        "*.tiff",
        "*.webp",
    ]

    # Get all image files in current directory
    image_files = []
    for extension in image_extensions:
        image_files.extend(glob.glob(extension))
        image_files.extend(glob.glob(extension.upper()))

    if not image_files:
        print("No image files found in current directory.")
        return

    print(f"Found {len(image_files)} image file(s) to process...")

    # Process each image
    for image_file in image_files:
        reduce_image_size(image_file)

    print("All images processed!")


if __name__ == "__main__":
    main()
