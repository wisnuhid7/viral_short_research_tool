import express from 'express';
import cors from 'cors';
import { config } from './lib/config.js';
import { logger } from './lib/logger.js';
import { setQuotaLimit } from './lib/quota-tracker.js';
import { AppError } from './lib/errors.js';
import { getDb, closeDb } from './db/schema.js';
import { searchRouter } from './routes/search.js';
import { summariesRouter } from './routes/summaries.js';
import { collectionsRouter } from './routes/collections.js';
import { exportRouter } from './routes/export.js';
import { quotaRouter } from './routes/quota.js';

const app = express();

// ─── Middleware ───────────────────────────────────────────

app.use(cors());
app.use(express.json());

// Request logging
app.use((req, _res, next) => {
  logger.debug(`${req.method} ${req.path}`);
  next();
});

// ─── Routes ──────────────────────────────────────────────

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use('/api/search', searchRouter);
app.use('/api/summaries', summariesRouter);
app.use('/api/collections', collectionsRouter);
app.use('/api/export', exportRouter);
app.use('/api/quota', quotaRouter);

// ─── Error Handler ───────────────────────────────────────

app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  if (err instanceof AppError) {
    logger.warn(`AppError: ${err.code}`, { message: err.message, status: err.statusCode });
    res.status(err.statusCode).json({ code: err.code, message: err.message });
    return;
  }

  const message = err instanceof Error ? err.message : 'Terjadi kesalahan yang tidak diketahui';
  logger.error('Unhandled error', { error: message });
  res.status(500).json({ code: 'INTERNAL_ERROR', message });
});

// ─── Start ───────────────────────────────────────────────

function start(): void {
  // Initialize DB
  getDb();

  // Set quota limit from config
  setQuotaLimit(config.youtube.dailyQuotaLimit);

  app.listen(config.port, () => {
    logger.info(`Server running on http://localhost:${config.port}`, {
      env: config.nodeEnv,
    });
  });
}

// Graceful shutdown
process.on('SIGINT', () => {
  logger.info('Shutting down...');
  closeDb();
  process.exit(0);
});

process.on('SIGTERM', () => {
  logger.info('Shutting down...');
  closeDb();
  process.exit(0);
});

start();
