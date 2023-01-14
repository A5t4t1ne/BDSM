from website import create_app

application = create_app()


if __name__ == "__main__":
    application.run(debug=True, port=80)
    # application.run(debug=False, host="0.0.0.0", port=80)