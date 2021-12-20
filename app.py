from flask import Flask, abort, redirect, render_template, request, session
import random

app = Flask("TBCOYL")
app.secret_key = ''.join([chr(random.randint(65,122)) for _ in range(64)])

import frontend


if __name__ == "__main__":
	app.run(port=80, debug=True)
