import { Router } from 'express';
import { createCollectionRequestSchema, addToCollectionRequestSchema } from 'shared';
import { ValidationError } from '../lib/errors.js';
import {
  createCollection,
  getCollections,
  getCollectionItems,
  addToCollection,
  removeFromCollection,
  deleteCollection,
} from '../db/queries.js';

export const collectionsRouter = Router();

/** GET /api/collections — list all collections */
collectionsRouter.get('/', (_req, res) => {
  const collections = getCollections();
  res.json(collections);
});

/** POST /api/collections — create a new collection */
collectionsRouter.post('/', (req, res, next) => {
  try {
    const parsed = createCollectionRequestSchema.safeParse(req.body);
    if (!parsed.success) {
      throw new ValidationError(
        `Input tidak valid: ${parsed.error.issues.map((i) => i.message).join(', ')}`
      );
    }

    const id = createCollection(parsed.data.name, parsed.data.description);
    res.status(201).json({ id, message: 'Koleksi berhasil dibuat.' });
  } catch (err) {
    next(err);
  }
});

/** GET /api/collections/:id/items — list items in a collection */
collectionsRouter.get('/:id/items', (req, res) => {
  const collectionId = parseInt(req.params['id'] ?? '', 10);
  if (isNaN(collectionId)) {
    res.status(400).json({ code: 'VALIDATION_ERROR', message: 'ID koleksi tidak valid.' });
    return;
  }
  const items = getCollectionItems(collectionId);
  res.json(items);
});

/** POST /api/collections/:id/items — add video to collection */
collectionsRouter.post('/:id/items', (req, res, next) => {
  try {
    const collectionId = parseInt(req.params['id'] ?? '', 10);
    if (isNaN(collectionId)) {
      throw new ValidationError('ID koleksi tidak valid.');
    }

    const parsed = addToCollectionRequestSchema.safeParse(req.body);
    if (!parsed.success) {
      throw new ValidationError(
        `Input tidak valid: ${parsed.error.issues.map((i) => i.message).join(', ')}`
      );
    }

    addToCollection(collectionId, parsed.data.videoId, parsed.data.tags, parsed.data.notes);
    res.status(201).json({ message: 'Video berhasil ditambahkan ke koleksi.' });
  } catch (err) {
    next(err);
  }
});

/** DELETE /api/collections/:id/items/:videoId — remove video from collection */
collectionsRouter.delete('/:id/items/:videoId', (req, res) => {
  const collectionId = parseInt(req.params['id'] ?? '', 10);
  const videoId = req.params['videoId'] ?? '';
  if (isNaN(collectionId) || !videoId) {
    res.status(400).json({ code: 'VALIDATION_ERROR', message: 'Parameter tidak valid.' });
    return;
  }
  removeFromCollection(collectionId, videoId);
  res.json({ message: 'Video berhasil dihapus dari koleksi.' });
});

/** DELETE /api/collections/:id — delete entire collection */
collectionsRouter.delete('/:id', (req, res) => {
  const collectionId = parseInt(req.params['id'] ?? '', 10);
  if (isNaN(collectionId)) {
    res.status(400).json({ code: 'VALIDATION_ERROR', message: 'ID koleksi tidak valid.' });
    return;
  }
  deleteCollection(collectionId);
  res.json({ message: 'Koleksi berhasil dihapus.' });
});
