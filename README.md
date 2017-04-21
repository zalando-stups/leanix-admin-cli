# leanix-admin

`leanix-admin` is a command line tool that can be used to backup and restore
  model files from [LeanIX](https://www.leanix.net).
Please note that it is only compatible with LeanIX 4.0 “Pathfinder”.

## CLI

### Installation

    pip3 install -r requirements.txt

### Get an API Token

Follow the steps in the
["Authentication" documentation](https://dev.leanix.net/v4.0/docs/authentication#section-generate-api-tokens)
to generate an API token. You will be asked for it in the next steps.
    
### Usage

Download the current model versions from LeanIX and store them on disk (in the current directory):  

    leanix-admin backup
    
Make the desired changes to the json files and upload them again:

    leanix-admin restore

#### Docker image

Build the docker image running: `docker build -t leanix-admin-cli .`

Run the leanix-admin-cli in a container:
`docker run --rm --name leanix-admin-cli -v $(pwd):/opt/models/ -e LX_API_TOKEN=$LX_API_TOKEN_LOCAL -ti --add-host local-eam.leanix.net:$(docker-machine ip) --add-host local-svc.leanix.net:$(docker-machine ip) leanix-admin-cli backup`

The **api token** can either be set via the env var `LX_API_TOKEN_LOCAL`.

For ease of use, you can add a function to your bash (or zsh) environment by adding the following function to you `~/.bashrc` (`~/.zshrc`)

```bash
leanix-admin-cli-local() {
    docker run --rm --name leanix-admin-cli -v $(pwd):/opt/models/ -e LX_API_TOKEN=$LX_API_TOKEN_LOCAL -ti --add-host local-eam.leanix.net:$(docker-machine ip) --add-host local-svc.leanix.net:$(docker-machine ip) leanix-admin-cli $1
}
```


## License

The MIT License (MIT)

Copyright © 2017 Zalando SE, https://tech.zalando.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This software is licensed under the MIT license (see below),
unless otherwise stated in the license files in higher directories (if any).
