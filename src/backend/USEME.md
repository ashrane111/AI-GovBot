after pip install -r requirements.txt
run `services.py` from root directory

open `localhost:8000/docs`

use the following in the body field to execute -
```json
{
  "messages": [
    {
    "role": "user",
    "content": "what is the take it down act?"
    }
  ]
}
```