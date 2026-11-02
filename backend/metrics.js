import {
	collectDefaultMetrics,
	Counter,
	Histogram,
	Registry,
} from "prom-client";

export const register = new Registry();

register.setDefaultLabels({ app: "mern-backend" });
collectDefaultMetrics({ register });

export const httpRequestsTotal = new Counter({
	name: "http_requests_total",
	help: "Total number of HTTP requests",
	labelNames: ["method", "route", "status"],
	registers: [register],
});

export const httpRequestDurationSeconds = new Histogram({
	name: "http_request_duration_seconds",
	help: "HTTP request duration in seconds",
	labelNames: ["method", "route", "status"],
	buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
	registers: [register],
});

export function metricsMiddleware(req, res, next) {
	const start = process.hrtime.bigint();

	res.on("finish", () => {
		const route = req.route ? `${req.baseUrl}${req.route.path}` : "unmatched";
		const duration = Number(process.hrtime.bigint() - start) / 1e9;

		httpRequestsTotal.inc({
			method: req.method,
			route,
			status: res.statusCode,
		});

		httpRequestDurationSeconds.observe(
			{
				method: req.method,
				route,
				status: res.statusCode,
			},
			duration,
		);
	});

	next();
}
