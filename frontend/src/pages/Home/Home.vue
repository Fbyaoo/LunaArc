<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import YourSpaceSection from '../../components/home/YourSpaceSection.vue'

import lunaArcLogo from '../../assets/home/lunaarc-logo.png'
import homeDoodles from '../../assets/home/home-doodles.png'
import homeSky from '../../assets/home/home-sky.png'

import {
  readingModes,
  sidebarNavigation,
} from '../../mocks/homeMock'

import {
  clearMockSession,
  getMockSession,
  type MockSession,
} from '../../mocks/authMock'

import type {
  NavigationId,
  ReadingMode,
  SidebarNavigationItem,
} from '../../types/home'

const router = useRouter()
const route = useRoute()

const session = ref<MockSession | null>(null)
const sidebarOpen = ref(false)
const activeModeId = ref<string | null>(null)
const pageReady = ref(false)

const user = computed(() => session.value?.user ?? null)

const userInitial = computed(() => {
  return user.value?.displayName?.charAt(0).toUpperCase() || 'L'
})

const usageText = computed(() => {
  if (!user.value) {
    return ''
  }

  if (user.value.plan === 'plus') {
    return 'Unlimited readings'
  }

  const remaining = user.value.freeReadingsRemaining

  return `${remaining} free reading${remaining === 1 ? '' : 's'} left today`
})

const planProgress = computed(() => {
  if (!user.value || user.value.plan === 'plus') {
    return 100
  }

  const total = user.value.dailyReadingLimit
  const remaining = user.value.freeReadingsRemaining

  if (total <= 0) {
    return 0
  }

  return Math.max(0, Math.min(100, (remaining / total) * 100))
})

const greeting = computed(() => {
  const hour = new Date().getHours()

  if (hour < 12) {
    return 'Good morning'
  }

  if (hour < 18) {
    return 'Good afternoon'
  }

  return 'Good evening'
})

const currentNavigationId = computed<NavigationId>(() => {
  if (route.path === '/home') {
    return 'home'
  }

  if (route.path.startsWith('/reading/daily')) {
    return 'daily-fortune'
  }

  if (route.path.startsWith('/reading/quick')) {
    return 'quick-question'
  }

  if (route.path.startsWith('/reading/deep')) {
    return 'deep-reading'
  }

  if (route.path.startsWith('/guide')) {
    return 'ai-guide'
  }

  if (route.path.startsWith('/saved-readings')) {
    return 'saved'
  }

  if (route.path.startsWith('/history')) {
    return 'history'
  }

  if (route.path.startsWith('/subscription')) {
    return 'subscription'
  }

  if (route.path.startsWith('/settings')) {
    return 'settings'
  }

  if (route.path.startsWith('/profile')) {
    return 'profile'
  }

  return 'home'
})

function scrollToReadingModes(): void {
  const readingSection = window.document.querySelector('#reading-modes')

  if (!(readingSection instanceof HTMLElement)) {
    return
  }

  readingSection.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

function navigateTo(item: SidebarNavigationItem): void {
  sidebarOpen.value = false
  void router.push(item.route)
}

function openReadingMode(mode: ReadingMode): void {
  activeModeId.value = mode.id

  window.setTimeout(() => {
    void router.push(mode.route)
  }, 280)
}

function openUpgrade(): void {
  void router.push('/subscription')
}

function logout(): void {
  clearMockSession()
  void router.replace('/')
}

onMounted(() => {
  session.value = getMockSession()

  window.requestAnimationFrame(() => {
    pageReady.value = true
  })
})
</script>

<template>
  <div
    class="home-page"
    :class="{
      'home-page--ready': pageReady,
      'home-page--sidebar-open': sidebarOpen,
    }"
  >
    <button
      class="mobile-menu-button"
      type="button"
      aria-label="Open navigation"
      :aria-expanded="sidebarOpen"
      @click="sidebarOpen = !sidebarOpen"
    >
      <span />
      <span />
    </button>

    <button
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      type="button"
      aria-label="Close navigation"
      @click="sidebarOpen = false"
    />

    <aside class="home-sidebar" aria-label="Main navigation">
      <header class="sidebar-brand">
        <img
          :src="lunaArcLogo"
          class="sidebar-brand__logo"
          alt="LunaArc"
        />
      </header>

      <button
        class="user-card"
        type="button"
        @click="router.push('/profile')"
      >
        <span class="user-card__avatar">
          {{ userInitial }}
        </span>

        <span class="user-card__content">
          <strong>{{ user?.displayName ?? 'Luna' }}</strong>
          <small>{{ user?.planLabel ?? 'Free Plan' }}</small>
        </span>

        <svg
          class="user-card__arrow"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path d="m9 6 6 6-6 6" />
        </svg>
      </button>

      <section
        v-if="user?.plan !== 'plus'"
        class="subscription-card"
      >
        <span class="subscription-card__orb" />

        <p class="subscription-card__eyebrow">
          LUNAARC PLUS
        </p>

        <h2>Unlock deeper insight.</h2>

        <p>
          Unlimited readings, full history and longer AI guidance.
        </p>

        <button type="button" @click="openUpgrade">
          Explore Plus
          <span aria-hidden="true">→</span>
        </button>
      </section>

      <section
        v-else
        class="subscription-card subscription-card--active"
      >
        <p class="subscription-card__eyebrow">
          CURRENT PLAN
        </p>

        <h2>LunaArc Plus</h2>

        <p>
          Your universe is fully open.
        </p>

        <button type="button" @click="openUpgrade">
          Manage plan
          <span aria-hidden="true">→</span>
        </button>
      </section>

      <nav class="sidebar-navigation">
        <section
          v-for="group in sidebarNavigation"
          :key="group.id"
          class="navigation-group"
        >
          <p class="navigation-group__label">
            {{ group.label }}
          </p>

          <button
            v-for="item in group.items"
            :key="item.id"
            class="navigation-item"
            :class="{
              'navigation-item--active':
                currentNavigationId === item.id,
            }"
            type="button"
            @click="navigateTo(item)"
          >
            <span class="navigation-item__icon">
              <svg
                v-if="item.icon === 'home'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="m3 11 9-7 9 7v9H5v-9" />
                <path d="M9 20v-6h6v6" />
              </svg>

              <svg
                v-else-if="item.icon === 'sparkle'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="m12 2 1.7 5.2L19 9l-5.3 1.8L12 16l-1.7-5.2L5 9l5.3-1.8L12 2Z" />
                <path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z" />
              </svg>

              <svg
                v-else-if="item.icon === 'question'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="9" />
                <path d="M9.7 9a2.5 2.5 0 0 1 4.8 1c0 2-2.5 2.2-2.5 4" />
                <path d="M12 18h.01" />
              </svg>

              <svg
                v-else-if="item.icon === 'cards'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <rect x="5" y="3" width="12" height="17" rx="2" />
                <path d="m9 8 2-2 2 2-2 2-2-2Z" />
                <path d="m10 20 7.5-2.2a2 2 0 0 0 1.4-2.4L16 5" />
              </svg>

              <svg
                v-else-if="item.icon === 'guide'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M4 5h16v11H8l-4 4V5Z" />
                <path d="M8 9h8M8 13h5" />
              </svg>

              <svg
                v-else-if="item.icon === 'history'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
                <path d="M3 3v5h5" />
                <path d="M12 7v5l3 2" />
              </svg>

              <svg
                v-else-if="item.icon === 'bookmark'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M6 3h12v18l-6-4-6 4V3Z" />
              </svg>

              <svg
                v-else-if="item.icon === 'profile'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle cx="12" cy="8" r="4" />
                <path d="M4 21a8 8 0 0 1 16 0" />
              </svg>

              <svg
                v-else-if="item.icon === 'subscription'"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M4 7h16v11H4V7Z" />
                <path d="M4 10h16" />
                <path d="M8 15h3" />
              </svg>

              <svg
                v-else
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v3M12 19v3M4.9 4.9 7 7M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1 7 17M17 7l2.1-2.1" />
              </svg>
            </span>

            <span>{{ item.label }}</span>
          </button>
        </section>
      </nav>

      <footer class="sidebar-footer">
        <div class="usage-status">
          <div class="usage-status__copy">
            <span>{{ usageText }}</span>
            <small v-if="user?.plan !== 'plus'">
              Resets tomorrow
            </small>
          </div>

          <div
            v-if="user?.plan !== 'plus'"
            class="usage-status__track"
          >
            <span :style="{ width: `${planProgress}%` }" />
          </div>
        </div>

        <button
          class="logout-button"
          type="button"
          @click="logout"
        >
          Log out
        </button>
      </footer>
    </aside>

    <main class="home-content">
      <section
        class="home-hero"
        :style="{ backgroundImage: `url(${homeSky})` }"
      >
        <div class="hero-atmosphere" />

        <div class="hero-toolbar">
          <div>
            <p>{{ greeting }}, {{ user?.displayName ?? 'Luna' }}.</p>
            <span>Welcome back to your inner universe.</span>
          </div>

          <button
            class="hero-profile-button"
            type="button"
            aria-label="Open profile"
            @click="router.push('/profile')"
          >
            {{ userInitial }}
          </button>
        </div>

        <div class="hero-brand">
          <img
            :src="lunaArcLogo"
            alt="LunaArc"
          />

          <p>
            What would you like to ask the universe today?
          </p>
        </div>

        <button
          class="hero-scroll-hint"
          type="button"
          aria-label="Scroll to readings"
          @click="scrollToReadingModes"
        >
          <span aria-hidden="true" />
          Explore
        </button>
      </section>

      <section
        id="reading-modes"
        class="reading-section"
      >
        <header class="section-heading">
          <p>CHOOSE A PATH</p>
          <h1>Begin with what feels close.</h1>
        </header>

        <div class="reading-mode-grid">
          <button
            v-for="(mode, index) in readingModes"
            :key="mode.id"
            class="reading-mode"
            :class="[
              `reading-mode--${mode.tone}`,
              {
                'reading-mode--selected':
                  activeModeId === mode.id,
                'reading-mode--muted':
                  activeModeId && activeModeId !== mode.id,
              },
            ]"
            type="button"
            :style="{
              '--mode-delay': `${index * 90}ms`,
            }"
            @click="openReadingMode(mode)"
          >
            <span class="reading-mode__orb">
              <span />
            </span>

            <span class="reading-mode__copy">
              <strong>{{ mode.title }}</strong>
              <small>{{ mode.eyebrow }}</small>
              <small>{{ mode.description }}</small>
            </span>

            <span class="reading-mode__arrow">
              →
            </span>
          </button>
        </div>

        <img
          :src="homeDoodles"
          class="reading-doodles"
          alt=""
          aria-hidden="true"
        />
      </section>

      <YourSpaceSection />

      <footer class="home-footer">
        <img :src="lunaArcLogo" alt="LunaArc" />

        <p>
          LunaArc readings are designed for reflection and
          entertainment, not professional advice.
        </p>
      </footer>
    </main>
  </div>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(html) {
  scroll-behavior: smooth;
}

:global(body) {
  margin: 0;
  min-width: 320px;
  background: #071b55;
  color: #183d76;
  font-family:
    Arial,
    "Helvetica Neue",
    Helvetica,
    sans-serif;
}

:global(button),
:global(input) {
  font: inherit;
}

:global(button) {
  -webkit-tap-highlight-color: transparent;
}

.home-page {
  --sidebar-width: 286px;
  --blue: #245cab;
  --deep-blue: #071b55;
  --soft-blue: #567db8;
  --cream: #f6f0e6;
  --white: #fffdf8;
  overflow-x: hidden;
  overflow-y: visible;
  min-height: 100vh;
  touch-action:pan-y;
  background: var(--deep-blue);
}

.home-sidebar {
  position: fixed;
  z-index: 30;
  top: 14px;
  bottom: 14px;
  left: 14px;

  display: flex;
  width: var(--sidebar-width);
  flex-direction: column;
  overflow: hidden;

  padding: 22px 14px 14px;

  border: 1px solid rgb(255 255 255 / 58%);
  border-radius: 30px;

  background: rgb(249 249 248 / 82%);
  box-shadow:
    0 24px 70px rgb(4 20 66 / 18%),
    inset 0 1px 0 rgb(255 255 255 / 78%);

  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);

  opacity: 0;
  transform: translateX(-18px);
  transition:
    opacity 800ms ease,
    transform 900ms cubic-bezier(.22, .8, .22, 1);
}

.home-page--ready .home-sidebar {
  opacity: 1;
  transform: translateX(0);
}

.sidebar-brand {
  display: flex;
  min-height: 54px;
  align-items: center;
  padding: 0 10px 10px;
}

.sidebar-brand__logo {
  width: 118px;
  height: auto;
  filter: brightness(.35) saturate(.7);
}

.user-card {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 11px;

  padding: 10px;

  border: 0;
  border-radius: 17px;
  background: transparent;
  color: #173a72;
  text-align: left;
  cursor: pointer;

  transition:
    background-color 260ms ease,
    transform 260ms ease;
}

.user-card:hover {
  background: rgb(37 91 170 / 7%);
  transform: translateY(-1px);
}

.user-card__avatar,
.hero-profile-button {
  display: grid;
  place-items: center;

  border: 1px solid rgb(255 255 255 / 70%);
  border-radius: 50%;

  background:
    linear-gradient(
      145deg,
      rgb(46 103 183 / 96%),
      rgb(117 147 195 / 88%)
    );

  color: white;
  box-shadow:
    0 8px 22px rgb(20 65 137 / 24%),
    inset 0 1px 0 rgb(255 255 255 / 40%);
}

.user-card__avatar {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  font-size: 16px;
  font-weight: 700;
}

.user-card__content {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 3px;
}

.user-card__content strong {
  overflow: hidden;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-card__content small {
  color: rgb(27 58 108 / 56%);
  font-size: 11px;
}

.user-card__arrow {
  width: 16px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
  opacity: .4;
}

.subscription-card {
  position: relative;
  overflow: hidden;
  margin: 14px 4px 16px;
  padding: 16px;

  border: 1px solid rgb(255 255 255 / 72%);
  border-radius: 21px;

  background:
    linear-gradient(
      145deg,
      rgb(225 235 250 / 88%),
      rgb(247 242 231 / 92%)
    );

  box-shadow:
    0 13px 30px rgb(15 57 121 / 11%),
    inset 0 1px 0 rgb(255 255 255 / 80%);
}

.subscription-card__orb {
  position: absolute;
  top: -32px;
  right: -25px;

  width: 92px;
  height: 92px;
  border-radius: 50%;

  background: rgb(37 91 170 / 13%);
  filter: blur(2px);
}

.subscription-card__eyebrow {
  margin: 0 0 8px;
  color: rgb(31 78 151 / 58%);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .15em;
}

.subscription-card h2 {
  position: relative;
  margin: 0;
  color: #173b75;
  font-size: 15px;
  line-height: 1.25;
}

.subscription-card p:not(.subscription-card__eyebrow) {
  position: relative;
  margin: 8px 0 13px;
  color: rgb(24 61 118 / 62%);
  font-size: 10px;
  line-height: 1.45;
}

.subscription-card button {
  position: relative;
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;

  padding: 9px 11px;

  border: 0;
  border-radius: 11px;

  background: #245cab;
  color: white;

  font-size: 10px;
  font-weight: 700;
  cursor: pointer;

  transition:
    transform 240ms ease,
    box-shadow 240ms ease;
}

.subscription-card button:hover {
  box-shadow: 0 8px 20px rgb(37 91 170 / 24%);
  transform: translateY(-1px);
}

.subscription-card--active {
  background:
    linear-gradient(
      145deg,
      rgb(223 233 248 / 92%),
      rgb(233 225 199 / 72%)
    );
}

.sidebar-navigation {
  flex: 1;
  overflow-y: auto;
  padding: 0 3px 16px;
  scrollbar-width: thin;
  scrollbar-color: rgb(33 74 137 / 22%) transparent;
}

.navigation-group + .navigation-group {
  margin-top: 15px;
}

.navigation-group__label {
  margin: 0 0 6px;
  padding: 0 11px;

  color: rgb(26 57 105 / 42%);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .12em;
}

.navigation-item {
  position: relative;
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;

  margin: 2px 0;
  padding: 9px 11px;

  border: 0;
  border-radius: 12px;

  background: transparent;
  color: rgb(19 48 94 / 73%);

  font-size: 12px;
  text-align: left;
  cursor: pointer;

  transition:
    background-color 240ms ease,
    color 240ms ease,
    transform 240ms ease;
}

.navigation-item:hover {
  background: rgb(36 92 171 / 6%);
  color: #1f519b;
  transform: translateX(2px);
}

.navigation-item--active {
  background: rgb(36 92 171 / 9%);
  color: #245cab;
  font-weight: 700;
}

.navigation-item--active::after {
  position: absolute;
  top: 50%;
  right: 9px;

  width: 5px;
  height: 5px;
  border-radius: 50%;

  background: #245cab;
  content: "";
  transform: translateY(-50%);
}

.navigation-item__icon {
  display: grid;
  width: 18px;
  height: 18px;
  flex: 0 0 18px;
  place-items: center;
}

.navigation-item__icon svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.6;
}

.sidebar-footer {
  padding: 12px 7px 2px;
  border-top: 1px solid rgb(23 57 109 / 8%);
}

.usage-status__copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.usage-status__copy span {
  color: #214e92;
  font-size: 10px;
  font-weight: 700;
}

.usage-status__copy small {
  color: rgb(28 61 112 / 42%);
  font-size: 9px;
}

.usage-status__track {
  height: 3px;
  overflow: hidden;
  margin-top: 9px;
  border-radius: 99px;
  background: rgb(36 92 171 / 9%);
}

.usage-status__track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #4f7fbe;
  transition: width 600ms ease;
}

.logout-button {
  margin-top: 12px;
  padding: 5px 0;
  border: 0;
  background: transparent;
  color: rgb(26 57 105 / 48%);
  font-size: 10px;
  cursor: pointer;
}

.logout-button:hover {
  color: #245cab;
}

.home-content {
  min-height: 100vh;
  margin-left: calc(var(--sidebar-width) + 28px);
  overflow: hidden;
  border-radius: 28px 0 0 28px;
  background: var(--cream);
}

.home-hero {
  position: relative;
  display: flex;

  width: 100%;
  min-height: 100vh;
  min-height: 100svh;

  align-items: center;
  justify-content: center;
  overflow: hidden;

  padding: 42px 54px;

  background-position: center;
  background-size: cover;
  color: white;
}

.hero-atmosphere {
  position: absolute;
  inset: 0;

  background:
    radial-gradient(
      circle at 70% 55%,
      rgb(136 160 204 / 14%),
      transparent 40%
    ),
    linear-gradient(
      180deg,
      rgb(3 16 68 / 6%),
      rgb(7 28 82 / 18%)
    );

  transform: scale(1.04);
}

.hero-toolbar {
  position: absolute;
  z-index: 2;
  top: 32px;
  right: 42px;
  left: 42px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  opacity: 0;
  transform: translateY(-10px);
  transition:
    opacity 800ms ease 280ms,
    transform 900ms cubic-bezier(.22, .8, .22, 1) 280ms;
}

.home-page--ready .hero-toolbar {
  opacity: 1;
  transform: translateY(0);
}

.hero-toolbar p {
  margin: 0 0 5px;
  font-size: 13px;
  font-weight: 700;
}

.hero-toolbar span {
  color: rgb(255 255 255 / 58%);
  font-size: 10px;
}

.hero-profile-button {
  width: 38px;
  height: 38px;
  border: 0;
  cursor: pointer;
}

.hero-brand {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  flex-direction: column;

  text-align: center;

  opacity: 0;
  transform: translateY(14px) scale(.985);
  transition:
    opacity 1100ms ease 180ms,
    transform 1300ms cubic-bezier(.2, .8, .2, 1) 180ms;
}

.home-page--ready .hero-brand {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.hero-brand img {
  width: clamp(260px, 31vw, 470px);
  height: auto;

  filter:
    drop-shadow(0 18px 30px rgb(1 15 58 / 18%));

  animation: logo-drift 7s ease-in-out infinite;
}

.hero-brand p {
  max-width: 460px;
  margin: 14px 0 0;

  color: rgb(255 255 255 / 68%);
  font-size: clamp(11px, 1.1vw, 15px);
  letter-spacing: .02em;
}

.hero-scroll-hint {
  position: absolute;
  z-index: 2;
  bottom: 25px;
  left: 50%;

  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 7px;

  border: 0;
  background: transparent;
  color: rgb(255 255 255 / 58%);

  font-size: 8px;
  letter-spacing: .15em;
  cursor: pointer;
  transform: translateX(-50%);
}

.hero-scroll-hint span {
  display: block;
  width: 1px;
  height: 22px;
  background:
    linear-gradient(
      to bottom,
      rgb(255 255 255 / 8%),
      rgb(255 255 255 / 75%)
    );
}

.reading-section {
  position: relative;
  display: flex;
  min-height: 100vh;
  min-height: 100svh;
  flex-direction: column;
  justify-content: center;

  overflow: hidden;
  padding: 72px 7vw 48px;

  background: #f8f1e7;
}

.section-heading {
  text-align: center;
}

.section-heading p {
  margin: 0 0 11px;
  color: rgb(40 86 153 / 48%);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .18em;
}

.section-heading h1 {
  margin: 0;
  color: #244e8c;
  font-size: clamp(24px, 3vw, 44px);
  font-weight: 500;
  letter-spacing: -.04em;
}

.reading-mode-grid {
  position: relative;
  z-index: 2;

  display: grid;
  max-width: 980px;
  margin: 66px auto 0;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}

.reading-mode {
  --mode-delay: 0ms;

  position: relative;
  display: flex;
  min-width: 0;
  align-items: center;
  flex-direction: column;

  padding: 18px 16px 30px;

  border: 0;
  border-radius: 28px;

  background: transparent;
  color: #295999;
  cursor: pointer;

  opacity: 0;
  transform: translateY(18px);
  transition:
    opacity 700ms ease var(--mode-delay),
    transform 700ms cubic-bezier(.22, .8, .22, 1)
      var(--mode-delay),
    background-color 300ms ease,
    filter 300ms ease;
}

.home-page--ready .reading-mode {
  opacity: 1;
  transform: translateY(0);
}

.reading-mode:hover {
  background: rgb(255 255 255 / 32%);
  transform: translateY(-5px);
}

.reading-mode--selected {
  background: rgb(255 255 255 / 45%);
  transform: scale(1.025);
}

.reading-mode--muted {
  filter: blur(1px);
  opacity: .45;
  transform: scale(.985);
}

.reading-mode__orb {
  position: relative;
  display: grid;
  width: 54px;
  height: 54px;
  place-items: center;

  margin-bottom: 27px;

  border: 1px solid rgb(255 255 255 / 72%);
  border-radius: 50%;

  background: rgb(64 107 170 / 88%);

  box-shadow:
    0 14px 30px rgb(31 78 151 / 15%),
    inset 0 1px 0 rgb(255 255 255 / 32%);

  transition:
    transform 350ms ease,
    box-shadow 350ms ease;
}

.reading-mode__orb span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgb(255 255 255 / 68%);
  opacity: 0;
  transform: scale(.4);
  transition:
    opacity 300ms ease,
    transform 350ms ease;
}

.reading-mode:hover .reading-mode__orb {
  box-shadow:
    0 17px 38px rgb(31 78 151 / 23%),
    0 0 0 9px rgb(46 99 177 / 5%);
  transform: scale(1.06);
}

.reading-mode:hover .reading-mode__orb span {
  opacity: 1;
  transform: scale(1);
}

.reading-mode--mist .reading-mode__orb {
  background: #c7c8cb;
}

.reading-mode--white .reading-mode__orb {
  background: #fffefa;
}

.reading-mode__copy {
  display: flex;
  align-items: center;
  flex-direction: column;
}

.reading-mode__copy strong {
  margin-bottom: 5px;
  font-size: 15px;
}

.reading-mode__copy small {
  font-size: 9px;
  font-weight: 800;
  line-height: 1.35;
  letter-spacing: .02em;
}

.reading-mode__arrow {
  margin-top: 20px;
  font-size: 16px;
  opacity: 0;
  transform: translateX(-5px);
  transition:
    opacity 260ms ease,
    transform 300ms ease;
}

.reading-mode:hover .reading-mode__arrow {
  opacity: .7;
  transform: translateX(0);
}

.reading-doodles {
  position: relative;
  z-index: 1;

  display: block;
  width: min(520px, 65vw);
  height: auto;

  margin: 52px auto 0;

  opacity: .64;
  transition:
    opacity 400ms ease,
    transform 500ms ease;
}

.reading-doodles:hover {
  opacity: .82;
  transform: translateY(-3px);
}

.home-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 30px;

  padding: 35px 6vw;

  background: #071b55;
  color: rgb(255 255 255 / 46%);
}

.home-footer img {
  width: 115px;
}

.home-footer p {
  max-width: 460px;
  margin: 0;
  font-size: 9px;
  line-height: 1.55;
  text-align: right;
}

.mobile-menu-button,
.sidebar-backdrop {
  display: none;
}

@keyframes logo-drift {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-7px);
  }
}

@media (max-width: 1120px) {
  .home-page {
    --sidebar-width: 250px;
  }


  .guide-card {
    min-height: 280px;
  }
}

@media (max-width: 820px) {
  .home-content {
    margin-left: 0;
    border-radius: 0;
  }

  .home-sidebar {
    top: 10px;
    bottom: 10px;
    left: 10px;

    width: min(286px, calc(100vw - 40px));

    opacity: 1;
    pointer-events: none;
    transform: translateX(calc(-100% - 24px));
  }

  .home-page--sidebar-open .home-sidebar {
    pointer-events: auto;
    transform: translateX(0);
  }

  .mobile-menu-button {
    position: fixed;
    z-index: 45;
    top: 18px;
    left: 18px;

    display: flex;
    width: 42px;
    height: 42px;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 5px;

    border: 1px solid rgb(255 255 255 / 38%);
    border-radius: 50%;

    background: rgb(255 255 255 / 16%);
    box-shadow: 0 10px 28px rgb(2 17 61 / 20%);

    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);

    cursor: pointer;
  }

  .mobile-menu-button span {
    width: 15px;
    height: 1px;
    background: white;
  }

  .sidebar-backdrop {
    position: fixed;
    z-index: 20;
    inset: 0;
    display: block;
    border: 0;
    background: rgb(4 16 51 / 38%);
    backdrop-filter: blur(4px);
  }

  .hero-toolbar {
    right: 20px;
    left: 74px;
  }

  .hero-toolbar > div {
    display: none;
  }

  .hero-toolbar {
    justify-content: flex-end;
  }

  .reading-mode-grid {
    grid-template-columns: 1fr;
    gap: 7px;
  }

  .reading-mode {
    display: grid;
    grid-template-columns: 54px 1fr 30px;
    gap: 18px;
    align-items: center;
    text-align: left;
  }

  .reading-mode__orb {
    margin-bottom: 0;
  }

  .reading-mode__copy {
    align-items: flex-start;
  }

  .reading-mode__arrow {
    margin-top: 0;
    opacity: .45;
  }

}

@media (max-width: 560px) {
  .home-hero {
    min-height: 68svh;
    padding: 30px 18px;
  }

  .hero-brand img {
    width: min(82vw, 360px);
  }

  .hero-brand p {
    max-width: 290px;
    font-size: 10px;
    line-height: 1.55;
  }

  .reading-section {
    padding: 74px 17px 50px;
  }

  .section-heading h1 {
    font-size: 29px;
  }

  .reading-mode {
    padding: 16px 12px;
  }

  .reading-doodles {
    width: 88vw;
  }

  .home-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .home-footer p {
    text-align: left;
  }
}

@media (prefers-reduced-motion: reduce) {
  :global(html) {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }
}
</style>