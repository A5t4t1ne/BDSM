from website import create_app

application = create_app()


if __name__ == "__main__":
    # app.run(debug=True)
    application.run(debug=False, port=80)