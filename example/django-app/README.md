# DevCycle Python Django Example App

Welcome to the DevCycle Python Django Example App, for sample usage with the [DevCycle Python Server SDK](https://github.com/DevCycleHQ/python-server-sdk).
To find Python SDK usage documentation, visit our [docs](https://docs.devcycle.com/docs/sdk/server-side-sdks/python#usage).

## Requirements.

Python 3.7+ and Django 4.2+

## Installation

```sh
pip install -r requirements.txt
```
(you may need to run `pip` with root permission: `sudo pip install -r requirements.txt`)

## Setup

See the `config/settings.py` file for the configuration of your SDK key in the `DEVCYCLE_SERVER_SDK_KEY` setting.

## Client Configuration

For convenience, a middleware implementation is used to add the DevCycle client to the request object, so you can access it in your views as `request.devcycle`. 

There are two examples of middleware, one for each type of DevCycle SDK: cloud bucketing and local bucketing. The middleware is configured in `config/settings.py`.

To customize the DevCycle client, you can update the appropriate function in the middleware. See `devcycle_test/middleware.py` for an example.

## Usage

To run the example app:
```sh
python manage.py migrate
python manage.py runserver
```
The server will start on port 8000. You can access the example app at http://localhost:8000.


## Variable Evaluation

An example of variable evaluation is done in `devcycle_test/views.py` where a user is created and the DevCycle client attached to the request is used to obtain a variable value.

```python
if request.devcycle.variable_value(user, variable_key, False):
    logger.info(f"{variable_key} is on")
    return HttpResponse("Hello, World! Your feature is on!")
```