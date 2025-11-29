# Normal use — auto cache inside ./tiles
python3 photo-mosaic.py -s dog.webp --tiles ./tiles

# Use tiles from current folder, save cache somewhere else
python3 photo-mosaic.py -s cat.webp --tiles ./ --db ./caches/real_photos.pkl

# Use a pre-built database from anywhere
python3 photo-mosaic.py -s anime.png --db ./caches/anime2025.pkl

# Rebuild a specific database
python3 photo-mosaic.py --build-db --db ./caches/nature.pkl --tiles ./nature_tiles -s sunset.webp

# Maximum variety, huge tiles
python3 photo-mosaic.py -s sky.webp --db ./caches/sky.pkl --no-repeat 10 --scale 12

--scale value
Each tile becomes this many pixels
Visual result
--scale 4
64 × 64 px
Very detailed, you can zoom in a lot
--scale 6
96 × 96 px
Balanced (good for most uses)
--scale 8 ← default
128 × 128 px
Classic photomosaic look
--scale 12
192 × 192 px
Bold, artistic, tiles very visible
--scale 16
256 × 256 px
Huge tiles — almost like a grid of photos

