# oshaberi

## local
```
docker build -t oshaberi .
docker run -d -p 8000:8000 oshaberi

docker run -it --rm --name oshaberi -v "$(pwd):/app" oshaberi /bin/bash
```

## TODO
https://chatgpt.com/share/6729d977-d6e4-8011-bfd6-7e791b0cbc1c

## ref
- [endpoint](https://oshaberi-17c056aaa88b.herokuapp.com/)
- [space endpoint](https://custom-ar-assets.nyc3.digitaloceanspaces.com)

## test
```
curl -X POST "https://oshaberi-17c056aaa88b.herokuapp.com/upload-list" \
    -F "marker=@/Users/hyakuzukamaya/Desktop/omikujiAR/assets/target-images/mendako.mind" \
    -F "models=@/Users/hyakuzukamaya/Desktop/omikujiAR/assets/models/chukichi.glb" \
    -F "models=@/Users/hyakuzukamaya/Desktop/omikujiAR/assets/models/daikichi.glb"
```