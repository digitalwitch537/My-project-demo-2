import express from "express";
import dotenv from "dotenv";
import path from "path";
import fs from "fs";

import { connectDB } from "./config/db.js";
import { metricsMiddleware, register } from "./metrics.js";

import productRoutes from "./routes/product.route.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

const __dirname = path.resolve();

app.use(express.json()); // allows us to accept JSON data in the req.body

app.get("/metrics", async (req, res) => {
	res.set("Content-Type", register.contentType);
	res.end(await register.metrics());
});

app.use(metricsMiddleware);

app.get("/api/health", (req, res) => {
	res.status(200).json({ status: "ok" });
});

app.use("/api/products", productRoutes);

const frontendDist = path.join(__dirname, "frontend", "dist");

if (process.env.NODE_ENV === "production" && fs.existsSync(frontendDist)) {
	app.use(express.static(frontendDist));
	app.get("*", (req, res) => {
		res.sendFile(path.join(frontendDist, "index.html"));
	});
}

app.listen(PORT, () => {
	connectDB();
	console.log("Server started at http://localhost:" + PORT);
});
