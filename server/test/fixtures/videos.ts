import type { Video } from 'shared';

export const mockVideos: Video[] = [
  {
    id: 'vid1',
    title: '5 AI Tools That Will Blow Your Mind #shorts',
    description: 'Check out these top AI tools for productivity in 2024!',
    channelId: 'ch1',
    channelTitle: 'Tech Wizard',
    publishedAt: new Date(Date.now() - 24 * 3600 * 1000).toISOString(), // 24 hours ago
    thumbnailUrl: 'https://i.ytimg.com/vi/vid1/hqdefault.jpg',
    duration: 45,
    viewCount: 150000,
    likeCount: 12000,
    commentCount: 450,
    tags: ['ai', 'tech', 'tools'],
    isShort: true,
    fetchedAt: new Date().toISOString(),
  },
  {
    id: 'vid2',
    title: 'How to make $100/day online without coding',
    description: 'Full breakdown of beginner side hustles.',
    channelId: 'ch2',
    channelTitle: 'Side Hustle Pro',
    publishedAt: new Date(Date.now() - 48 * 3600 * 1000).toISOString(), // 48 hours ago
    thumbnailUrl: 'https://i.ytimg.com/vi/vid2/hqdefault.jpg',
    duration: 58,
    viewCount: 300000,
    likeCount: 25000,
    commentCount: 800,
    tags: ['sidehustle', 'money', 'online'],
    isShort: true,
    fetchedAt: new Date().toISOString(),
  },
  {
    id: 'vid3',
    title: 'Brand new short just released',
    description: 'Fresh upload test',
    channelId: 'ch1',
    channelTitle: 'Tech Wizard',
    publishedAt: new Date(Date.now() - 1 * 3600 * 1000).toISOString(), // 1 hour ago (< 3 hours)
    thumbnailUrl: 'https://i.ytimg.com/vi/vid3/hqdefault.jpg',
    duration: 30,
    viewCount: 2000,
    likeCount: 100,
    commentCount: 10,
    tags: ['tech'],
    isShort: true,
    fetchedAt: new Date().toISOString(),
  }
];
