from website import create_app
import json

app = create_app()


if __name__ == "__main__":
    # test
    # with open('.\\heroes\\user_asdff\\aldarine_eibentanz_die_sucherin.json', 'r') as f:
    #     print(json.load(f))
    app.run(debug=False, host="0.0.0.0", port=5000)