# python-image-colors
The backend/api for an image color analysis application.
- Frontend code that consumes this api available here: https://gitlab.com/Itamar_gilboa/image-colors

## How it works


### Getting image colors steps
We get the top 10 most prominent colors from a given image

### Getting closest color steps
We get the closest available color in our database for a given color: rgb or hex


## API
The following endpoints are available:
#### analyze
Endpoint: /analyze
Method: POST
Request object:
```
{
    image: <imageFile>
}
```

#### closest color
Endpoint: /get_closes_color_<colorspace>?r=xx&g=xx&b=xx OR
/get_closes_color_<colorspace>?hex=xxx
Method: GET
Possible color spaces: rgb, lab, cmyk

## See it in action
- This code is currently hosted here: https://squid-app-5flef.ondigitalocean.app . It is publicly accessible and can be used with an api client or the frontend below
- Frontend hosted here (expect a chrome security warning, working on it): https://art-collections-color-analyzer.netlify.app/ 

## Running locally
#### Requirements:
- Docker
- An API client OR the frontend code shown above
- Access to a postgreSql database
- Copy the .env.example file with the connection info of above postgreSQL database
- Run the cisg script from within the docker container that will give you a text file with the insert scripts to run on your database.
