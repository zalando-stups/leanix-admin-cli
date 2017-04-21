# leanix-admin-cli

`leanix-admin` is a command line tool that can be used to backup and restore
  model files, tag groups and tags from [LeanIX](https://www.leanix.net).
Please note that it is only compatible with LeanIX 4.0 “Pathfinder”. It requires Python >= 3.6.1.

You can use a docker container to run the command, which ensures the command is executed with a proper Python version.

## CLI

### Installation

    pip3 install -r requirements.txt

### Get an API Token

Follow the steps in the
["Authentication" documentation](https://dev.leanix.net/v4.0/docs/authentication#section-generate-api-tokens)
to generate an API token. You will be asked for it in the next steps.
    
### Usage

Download the current model versions and tags from LeanIX and store them on disk (in the current directory):  

    leanix-admin backup
    
Make the desired changes to the json files and upload them again:

    leanix-admin restore

### Options & Environment Variables

	leanix-admin --log-level DEBUG backup \
	   --mtm-base-url https://demo-svc.leanix.net/services/mtm/v1 \
	   --api-token $LX_API_TOKEN \
	   --api-base-url https://demo.leanix.net/beta/api/v1

Each command line option also has a corresponding environment variable (in brackets):

* `--log-level (LOG_LEVEL)`: DEBUG, INFO, WARNING, ERROR, CRITICAL, see [Python Logging](https://docs.python.org/2/howto/logging.html)
* `--api-token (LX_API_TOKEN)`: LeanIX API Token, see ["Authentication" documentation](https://dev.leanix.net/v4.0/docs/authentication#section-generate-api-tokens)
* `--mtm-base-url (LX_MTM_BASE_URL)`: URL to MTM Service which allows to retrieve a valid access token from the API token
* `--api-base-url (LX_API_BASE_URL)`: URL to LeanIX Pathfinder API

#### Docker image

Build the docker image running:

	docker build -t leanix-admin-cli .

Run the leanix-admin-cli in a container:

	docker run --rm --name leanix-admin-cli -v $(pwd):/opt/models/ \
	 -e LX_API_TOKEN=$LX_API_TOKEN \
	 -e LX_API_BASE_URL=https://demo.leanix.net/beta/api/v1 \
	 -e LX_MTM_BASE_URL=https://demo-svc.leanix.net/services/mtm/v1 \
	 -ti leanix-admin-cli backup

Run the leanix-admin-cli in a container against your **local leanix development**:

	docker run --rm --name leanix-admin-cli -v $(pwd):/opt/models/ \
	 -e LX_API_TOKEN=XXX \
	 -e LX_API_BASE_URL=https://local-eam.leanix.net/beta/api/v1 \
	 -e LX_MTM_BASE_URL=https://local-svc.leanix.net/services/mtm/v1 \
	 --add-host local-eam.leanix.net:$(docker-machine ip) \
	 --add-host local-svc.leanix.net:$(docker-machine ip) \
	 -ti leanix-admin-cli backup

For ease of use, you can add a function to your bash (or zsh) environment by adding the following function to you `~/.bashrc` (`~/.zshrc`)

```bash
leanix-admin-cli-local() {
	docker run --rm --name leanix-admin-cli -v $(pwd):/opt/models/ \
	 -e LX_API_TOKEN=$LX_API_TOKEN \
	 -e LX_API_BASE_URL=https://demo.leanix.net/beta/api/v1 \
	 -e LX_MTM_BASE_URL=https://demo-svc.leanix.net/services/mtm/v1 \
	 -ti leanix-admin-cli backup
}
```

### Known issues

* **Wrong order of data model**: Python versions earlier than 3.X seem to change the order of the json data model.

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
