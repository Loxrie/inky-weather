import express from "express"

import * as weather from './routes/weather.js';

const app = express()
const port = process.env.PORT ?? "3001";

const router = express.Router({
    mergeParams: true
});

app.use(router);

app.listen(port, () => {
    console.log(`tiny-weather listening on ${port}`)
})

router.get('/weather/:id', weather.get());
