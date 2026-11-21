
from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO
import requests

app = Flask(__name__)

THUMBNAIL_API = "https://thumbnails.roblox.com/v1/assets"

FALLBACK_1 = [255, 180, 205]
FALLBACK_2 = [190, 165, 255]


@app.get("/")
def home():
    return "Duck CITY Album Color API is running"


@app.get("/colors")
def get_colors():
    asset_id = request.args.get("assetId", "").strip()

    if not asset_id.isdigit() or asset_id == "0":
        return jsonify({"error": "Invalid assetId"}), 400

    try:
        thumbnail = requests.get(
            THUMBNAIL_API,
            params={
                "assetIds": asset_id,
                "size": "420x420",
                "format": "Png",
                "returnPolicy": "PlaceHolder"
            },
            timeout=20
        )

        thumbnail.raise_for_status()

        data = thumbnail.json().get("data", [])

        if not data or not data[0].get("imageUrl"):
            return jsonify({
                "color1": FALLBACK_1,
                "color2": FALLBACK_2
            })

        image_response = requests.get(
            data[0]["imageUrl"],
            timeout=20
        )

        image_response.raise_for_status()

        image = Image.open(
            BytesIO(image_response.content)
        ).convert("RGB")

        image.thumbnail((100, 100))

        quantized = image.quantize(colors=8)
        palette = quantized.getpalette()
        counts = quantized.getcolors(10000)

        if not counts:
            raise Exception("Cannot analyze image")

        counts.sort(reverse=True)

        selected = []

        for count, index in counts:
            offset = index * 3
            rgb = tuple(palette[offset:offset + 3])

            if max(rgb) < 35:
                continue

            if min(rgb) > 235:
                continue

            if rgb not in selected:
                selected.append(rgb)

            if len(selected) >= 2:
                break

        if len(selected) == 0:
            selected = [
                tuple(FALLBACK_1),
                tuple(FALLBACK_2)
            ]
        elif len(selected) == 1:
            selected.append(selected[0])

        return jsonify({
            "color1": list(selected[0]),
            "color2": list(selected[1])
        })

    except Exception as error:
        app.logger.exception("Color analysis failed")

        return jsonify({
            "error": str(error)
        }), 500
