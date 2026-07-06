import dns from "dns";
import mongoose from "mongoose";

// Windows often blocks SRV lookups via the system resolver; public DNS works for Atlas.
dns.setServers(["8.8.8.8", "8.8.4.4", "1.1.1.1"]);
dns.setDefaultResultOrder("ipv4first");

interface MongooseCache {
  conn: typeof mongoose | null;
  promise: Promise<typeof mongoose> | null;
}

const globalForMongoose = globalThis as typeof globalThis & {
  mongooseCache?: MongooseCache;
};

function getCache(): MongooseCache {
  if (!globalForMongoose.mongooseCache) {
    globalForMongoose.mongooseCache = { conn: null, promise: null };
  }
  return globalForMongoose.mongooseCache;
}

/**
 * Cached Mongoose connection for Next.js serverless / dev hot reload.
 */
export async function connectDB(): Promise<typeof mongoose> {
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    throw new Error(
      "Please define the MONGODB_URI environment variable inside .env.local",
    );
  }

  const cache = getCache();

  if (cache.conn) {
    return cache.conn;
  }

  if (!cache.promise) {
    cache.promise = mongoose
      .connect(uri, {
        family: 4,
        serverSelectionTimeoutMS: 15000,
      })
      .then((mongooseInstance) => {
        console.log("[MongoDB] Connected successfully");
        return mongooseInstance;
      })
      .catch((err: unknown) => {
        console.error("[MongoDB] Connection failed:", err);
        cache.promise = null;
        throw err;
      });
  }

  cache.conn = await cache.promise;
  return cache.conn;
}
