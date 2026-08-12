export const kph = new RegExp(/(?:.*)?SpeedKph/i)
export const farenheit = new RegExp(/(?:.*)?TemperatureF/i)
export const abbreviation = new RegExp(/(?:.*)?Abbreviation/)
export const unwantedUV = new RegExp(/uvIndex(?!Text).*/)
export const unwatedText = new RegExp(
    /(?:windDirectionAbbreviation|windDirectionFull|enhancedWeatherDescription|precipitationProbabilityText|windDescription|precipitationProbabilityText|windDescription)/
)

const inDepthRemove = (regex: RegExp[], data: Object | Object[], stripNullValue = false): Object | Object[] => {
    if (Array.isArray(data)) {
        data.forEach((e) => inDepthRemove(regex, e, stripNullValue));
    } else if (data instanceof Object) {
        for (const key in data) {
            if (Array.isArray(data[key as keyof Object]) || data[key as keyof Object] instanceof Object) {
                inDepthRemove(regex, data[key as keyof Object], stripNullValue)
            } else {
                if (stripNullValue && !data[key as keyof Object]) {
                    delete data[key as keyof Object]
                } else {
                    regex.forEach(r => {
                        if (r.test(key)) {
                            delete data[key as keyof Object]
                        }
                    })
                }
            }
        }
    }
    return data
}

export default inDepthRemove