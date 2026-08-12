import type { RequestHandler } from "express-serve-static-core";

// import inDepthRemove, { kph, farenheit, abbreviation, unwantedUV, unwatedText } from "../lib/inDepthRemove.js";

interface OptimisedSummary {
  gustSpeedMph: number[];
  localDate: string[];
  maxTempC: number[];
  minTempC: number[];
  mostLikelyHighTemperatureC: number[];
  mostLikelyLowTemperatureC: number[];
  pollenIndexText: (string | null)[];
  pollutionIndexText: (string | null)[];
  precipitationProbabilityInPercent: (number | null)[]
  sunrise: string[];
  sunset: string[];
  uvIndexText: string[];
  weatherTypeText: string[];
  windDirection: string[];
  windSpeedMph: number[];
}

interface OptimisedResponse {
  name: string;
  isNight: boolean;
  issueDate: string;
  lastUpdated: string;
  summary: OptimisedSummary;
}

export interface BBCWeatherAggregatedResponse {
  forecasts: ForecastDay[];
  isNight: boolean;
  issueDate: string;
  lastUpdated: string;
  location: WeatherLocation;
  message: string;
  night: boolean;
}

export interface WeatherLocation {
  id: string; // e.g. "2638867"
  name: string; // e.g. "St Albans"
  container: string; // e.g. "Hertfordshire"
  latitude: number;
  longitude: number;
}

export interface ForecastDay {
  detailed?: DetailedForecast;
  summary: SummaryForecast;
}

export interface DetailedForecast {
  issueDate: string;
  lastUpdated: string;
  reports: DetailedReport[];
}

export interface DetailedReport {
  enhancedWeatherDescription: string;
  extendedWeatherType: number;
  feelsLikeTemperatureC: number;
  feelsLikeTemperatureF: number;
  gustSpeedKph: number;
  gustSpeedMph: number;
  humidity: number;
  localDate: string; // YYYY-MM-DD
  precipitationProbabilityInPercent: number;
  precipitationProbabilityText: string;
  pressure: number;
  temperatureC: number;
  temperatureF: number;
  timeslot: string; // HH:MM
  timeslotLength: number;
  visibility: string; // e.g. "Very Good", "Good", "Moderate"
  weatherType: number;
  weatherTypeText: string;
  windDescription: string;
  windDirection: string; // Can be a standard string like "ESE" or custom fallback value like "-99"
  windDirectionAbbreviation: string; // e.g. "ESE" or "-99"
  windDirectionFull: string; // e.g. "east-south-easterly" or "Direction not available"
  windSpeedKph: number;
  windSpeedMph: number;
}

export interface SummaryForecast {
  issueDate: string;
  lastUpdated: string;
  report: SummaryReport;
}

export interface SummaryReport {
  enhancedWeatherDescription: string;
  gustSpeedKph: number;
  gustSpeedMph: number;
  localDate: string; // YYYY-MM-DD
  lowermaxTemperatureC: number | null;
  lowermaxTemperatureF: number | null;
  lowerminTemperatureC: number | null;
  lowerminTemperatureF: number | null;
  maxTempC: number;
  maxTempF: number;
  minTempC: number;
  minTempF: number;
  mostLikelyHighTemperatureC: number;
  mostLikelyHighTemperatureF: number;
  mostLikelyLowTemperatureC: number;
  mostLikelyLowTemperatureF: number;
  pollenIndex: number | null;
  pollenIndexBand: string | null; // e.g. "LOW", "MODERATE"
  pollenIndexIconText: string | null; // e.g. "L", "M"
  pollenIndexText: string | null;
  pollutionIndex: number | null;
  pollutionIndexBand: string | null;
  pollutionIndexIconText: string | null;
  pollutionIndexText: string | null;
  precipitationProbabilityInPercent: number;
  precipitationProbabilityText: string;
  sunrise: string; // HH:MM
  sunset: string;  // HH:MM
  uppermaxTemperatureC: number | null;
  uppermaxTemperatureF: number | null;
  upperminTemperatureC: number | null;
  upperminTemperatureF: number | null;
  uvIndex: number;
  uvIndexBand: string; // e.g. "MODERATE", "HIGH", "VERY_HIGH"
  uvIndexIconText: string; // e.g. "M", "H", "VH"
  uvIndexText: string;
  weatherType: number;
  weatherTypeText: string;
  windDescription: string;
  windDirection: string;
  windDirectionAbbreviation: string;
  windDirectionFull: string;
  windSpeedKph: number;
  windSpeedMph: number;
}

export function get(): RequestHandler {
  return async (req, res, next) => {
    console.log(req.headers);
    if (req.headers && req.headers.authorization) {
      if (req.headers.authorization !== `Bearer ${process.env.BEARER}`) {
        res.status(403).json({ status: "unauthorised" });
        return;
      }
    }
    const url = `https://weather-broker-cdn.api.bbci.co.uk/en/forecast/aggregated/${req.params.id}`;
    const response = await fetch(url);
    const text = await response.text();
    const data = await JSON.parse(text) as BBCWeatherAggregatedResponse;

    const summaryKeys: (keyof SummaryReport)[] = [
      "gustSpeedMph",
      "localDate",
      "maxTempC",
      "minTempC",
      "mostLikelyHighTemperatureC",
      "mostLikelyLowTemperatureC",
      "pollenIndexText",
      "pollutionIndexText",
      "precipitationProbabilityInPercent",
      "sunrise",
      "sunset",
      "uvIndexText",
      "weatherTypeText",
      "windDirection",
      "windSpeedMph",
    ];

    const optimised: OptimisedResponse = {
      name: data["location"]["name"],
      isNight: data["isNight"],
      issueDate: data["issueDate"],
      lastUpdated: data["lastUpdated"],
      summary: {
        gustSpeedMph: [],
        localDate: [],
        maxTempC: [],
        minTempC: [],
        mostLikelyHighTemperatureC: [],
        mostLikelyLowTemperatureC: [],
        pollenIndexText: [],
        pollutionIndexText: [],
        precipitationProbabilityInPercent: [],
        sunrise: [],
        sunset: [],
        uvIndexText: [],
        weatherTypeText: [],
        windDirection: [],
        windSpeedMph: []
      },
    };

    data.forecasts.forEach(forecast => {
      const summary = forecast.summary.report;
      
      summaryKeys.forEach(key => {
        if (key in summary) {
          const value = summary[key];
          (optimised.summary[key as keyof OptimisedSummary] as any[]).push(value);
        }
      });
    });

    res.status(200).json(optimised);
  };
}
