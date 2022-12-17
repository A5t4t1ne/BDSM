from website import create_app

application = create_app()


if __name__ == "__main__":
    # app.run(debug=True)
    application.run(debug=False, host="0.0.0.0", port=5000)