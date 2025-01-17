from(bucket: "fueljournal")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fuel_prices")
  |> filter(fn: (r) => r["_field"] == "diesel" or r["_field"] == "dieselPremium" or r["_field"] == "sp95" or r["_field"] == "sp98")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")