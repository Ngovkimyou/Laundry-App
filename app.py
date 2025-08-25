from flask import Flask, render_template, request
import requests
from datetime import datetime
from pytz import timezone

app = Flask(__name__)

API_KEY = 'b11d134a90f74493be653218250105'
FORECAST_URL = "http://api.weatherapi.com/v1/forecast.json?"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city = request.form.get("city")
        if city:
            return get_weather_data(city)
    return render_template("index.html")

def get_weather_data(city_name):
    url = f"{FORECAST_URL}key={API_KEY}&q={city_name}&days=1"
    try:
        response = requests.get(url).json()
    except requests.exceptions.RequestException as e:
        return render_template("index.html", error=f"Request failed: {str(e)}")

    if "error" in response:
        return render_template("index.html", error="Invalid city or API error")

    try:
        current = response['current']
        forecast = response['forecast']['forecastday'][0]
        localtime_str = response['location']['localtime']  # Example: "2025-04-26 15:30"
        # Convert it into datetime
        localtime_dt = datetime.strptime(localtime_str, "%Y-%m-%d %H:%M")
        formatted_time = localtime_dt.strftime("%A, %#I:%M %p")  # Example: "Saturday, 3:30 PM"
        data = {
            "city": city_name.title(),
            "temperature": current['temp_c'],
            "condition": current['condition']['text'],
            "feels_like": current['feelslike_c'],
            "humidity": current['humidity'],
            "wind_speed": current['wind_kph'],
            "pressure": current['pressure_mb'],
            "sunrise": forecast['astro']['sunrise'],
            "sunset": forecast['astro']['sunset'],
            "current_time": formatted_time,
            "hours": forecast['hour'],
        }

        # Laundry suggestion
        condition = current['condition']['text'].lower()
        humidity = current['humidity']
        wind_speed = current['wind_kph']

        if any(x in condition for x in ["rain", "thunderstorm", "snow"]):
            data["suggestion"] = "❌ Not a good day for laundry. Expect precipitation."
        elif humidity > 80:
            data["suggestion"] = "⚠️ It's humid today. Clothes might dry slowly."
        elif wind_speed > 15:
            data["suggestion"] = "✅ Windy and dry – great for outdoor drying!"
        else:
            data["suggestion"] = "✅ Weather looks fine for laundry."

        return render_template("weather.html", data=data)

    except KeyError as e:
        return render_template("index.html", error=f"Response parsing error: {e}")

@app.route("/laundry-details/<city>")
def laundry_details(city):
    url = f"{FORECAST_URL}key={API_KEY}&q={city}&days=1"
    try:
        response = requests.get(url).json()
    except requests.exceptions.RequestException as e:
        return render_template("error.html", message=f"Failed to fetch forecast: {e}")

    if "error" in response:
        return render_template("error.html", message=f"Invalid city: {city}")

    hours = response['forecast']['forecastday'][0].get("hour", [])
    time_precip = [(h['time'][11:], h['precip_mm']) for h in hours]

    best_hours = [t for t, p in time_precip if p < 0.5]
    tip = f"Best to start laundry after {best_hours[0]} 🮺☀️" if best_hours else "Oh no! 🌧️ No dry windows today."

    return render_template("laundry.html", city=city.title(), forecast=time_precip, tip=tip)

if __name__ == '__main__':
    # app.run(host='0.0.0.0',debug=True)
    app.run(debug=True)
