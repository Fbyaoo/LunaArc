import type {
  ReadingMode,
  SidebarNavigationGroup,
} from '../types/home'

export const readingModes: ReadingMode[] = [
  {
    id: 'daily-fortune',
    title: 'Daily Fortune',
    eyebrow: '# ONE CARD',
    description: "FOR TODAY'S ENERGY",
    route: '/reading/daily',
    tone: 'blue',
  },
  {
    id: 'quick-question',
    title: 'Quick Question',
    eyebrow: '# ONE CARD',
    description: 'AT YOUR SERVICE',
    route: '/reading/quick',
    tone: 'mist',
  },
  {
    id: 'deep-reading',
    title: 'Deep Reading',
    eyebrow: '# THREE CARDS',
    description: 'EXPLORE INSIDE MIND',
    route: '/reading/deep',
    tone: 'white',
  },
]

export const sidebarNavigation: SidebarNavigationGroup[] = [
  {
    id: 'explore',
    label: 'EXPLORE',
    items: [
      {
        id: 'home',
        label: 'Home',
        icon: 'home',
        route: '/home',
      },
      {
        id: 'daily-fortune',
        label: 'Daily Fortune',
        icon: 'sparkle',
        route: '/reading/daily',
      },
      {
        id: 'quick-question',
        label: 'Quick Question',
        icon: 'question',
        route: '/reading/quick',
      },
      {
        id: 'deep-reading',
        label: 'Deep Reading',
        icon: 'cards',
        route: '/reading/deep',
      },
    ],
  },
  {
    id: 'your-space',
    label: 'YOUR SPACE',
    items: [
      {
        id: 'ai-guide',
        label: 'AI Tarot Guide',
        icon: 'guide',
        route: '/guide',
      },
      {
        id: 'history',
        label: 'Reading History',
        icon: 'history',
        route: '/history',
      },
      {
        id: 'saved',
        label: 'Saved Readings',
        icon: 'bookmark',
        route: '/saved-readings',
      },
    ],
  },
  {
    id: 'account',
    label: 'ACCOUNT',
    items: [
      {
        id: 'profile',
        label: 'Profile',
        icon: 'profile',
        route: '/profile',
      },
      {
        id: 'subscription',
        label: 'Subscription',
        icon: 'subscription',
        route: '/subscription',
      },
      {
        id: 'settings',
        label: 'Settings',
        icon: 'settings',
        route: '/settings',
      },
    ],
  },
]
