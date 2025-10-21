<template>
  <div class="daily-inspiration">
    <!-- Toast notification -->
    <div class="toast" :class="{ 'toast-show': showToast }">
      📋 Copied to clipboard!
    </div>
    
    <header class="header" :class="{ 'header-minimized': isScrolled }">
      <div class="container">
        <h1 class="title">🏛️ Daily Architect Wisdom</h1>
        <div class="date-info" v-show="!isScrolled || !isMobile">
          <span class="current-date">{{ formatDate(currentDate) }}</span>
          <span class="day-counter" v-if="isDeveloperMode">Day {{ currentDayNumber }} of {{ totalArticles }}</span>
        </div>
        
        <!-- Combined navigation and actions bar -->
        <div class="header-controls" v-if="hasArticlesAvailable">
          <!-- Navigation buttons (left aligned) -->
          <div class="header-navigation">
            <button 
              @click="goToPreviousDay" 
              :disabled="!canGoToPreviousDay"
              class="nav-button prev"
              title="Previous Day"
            >
              {{ previousButtonText }}
            </button>
            
            <button @click="goToToday" class="nav-button today" title="Today">
              Today
            </button>
            
            <button 
              @click="goToNextDay" 
              :disabled="!canGoToNextDay"
              class="nav-button next"
              :title="nextButtonTooltip"
            >
              {{ nextButtonText }}
            </button>
          </div>
          
          <!-- Share button and dev tools (right aligned) -->
          <div class="header-actions" v-if="currentArticle">
            <!-- Developer mode article selector -->
            <div class="dev-selector" v-if="isDeveloperMode">
              <select 
                @change="selectArticle" 
                :value="currentDayNumber - 1"
                class="article-selector"
                title="Select article (Dev Mode)"
              >
                <option 
                  v-for="(article, index) in articles" 
                  :key="index" 
                  :value="index"
                >
                  {{ index + 1 }}. {{ article.title }}
                </option>
              </select>
            </div>
            
            <button 
              @click="shareArticle" 
              class="share-button"
              title="Share today's wisdom"
            >
              📤 Share
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="main-content">
      <div class="container">
        <!-- No articles available yet -->
        <div class="no-articles" v-if="!hasArticlesAvailable">
          <div class="no-articles-content">
            <h2 class="no-articles-title">Coming Soon</h2>
            <div class="countdown" v-if="daysUntilStart > 0">
              <div class="countdown-number">{{ daysUntilStart }}</div>
              <div class="countdown-label">{{ daysUntilStart === 1 ? 'day' : 'days' }} to go!</div>
            </div>
            <p class="no-articles-message">
              Daily Architect Wisdom starts on
              <strong>{{ formatDate(new Date(START_DATE)) }}</strong>
            </p>
            <p class="no-articles-subtitle">
              Check back then for your first dose of architecture wisdom!
            </p>
          </div>
        </div>

        <!-- Weekend message -->
        <div class="weekend-message" v-else-if="isWeekendAfterStart">
          <div class="weekend-content">
            <h2 class="weekend-title">📅 It's the Weekend!</h2>
            <p class="weekend-text">
              New articles are revealed on <strong>weekdays only</strong>. 
              The next article will be available on 
              <strong>{{ formatDate(nextWeekdayDate) }}</strong>.
            </p>
            <p class="weekend-subtitle">
              In the meantime, you can browse the previous week's articles using the navigation buttons above!
            </p>
          </div>
        </div>

        <!-- Article content -->
        <article class="article" v-else-if="currentArticle">
          <div class="article-header">
            <h2 class="article-title">{{ currentArticle.title }}</h2>
            <p class="article-author">by {{ currentArticle.author }}</p>
            <p class="article-reading-time">{{ estimatedReadingTime }}</p>
          </div>
          
          <div class="article-content" v-html="renderedContent"></div>
        </article>
      </div>
    </main>
    
    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <p class="attribution">
            📖 Articles sourced from
            <strong>"97 Things Every Software Architect Should Know"</strong>
          </p>
          <p class="purchase-link">
            <a
              href="https://www.oreilly.com/library/view/97-things-every/9780596800611/"
              target="_blank"
              rel="noopener noreferrer"
              class="book-link"
            >
              📚 Get the full book from O'Reilly
            </a>
          </p>
          <p class="credit">
            Full credit to the original authors and contributors
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import articlesData from '../data/articles.json'

// Configuration
const START_DATE = new Date('2025-10-20') // Articles start date
const isDeveloperMode = import.meta.env.DEV // Enable developer features in development

const articles = articlesData.inspiration
const totalArticles = articles.length
const currentDate = ref(new Date())
const isScrolled = ref(false)
const isMobile = ref(false)
const showToast = ref(false)
const lastScrollY = ref(0)

// Helper function to check if a date is a weekday
const isWeekday = (date) => {
  const day = date.getDay()
  return day >= 1 && day <= 5 // Monday = 1, Friday = 5
}

// Calculate weekdays between two dates
const getWeekdaysBetween = (startDate, endDate) => {
  let count = 0
  let current = new Date(startDate)
  
  while (current <= endDate) {
    if (isWeekday(current)) {
      count++
    }
    current.setDate(current.getDate() + 1)
  }
  
  return count
}

// Get the article index for a given date
const getArticleIndexForDate = (date) => {
  if (date < START_DATE) return null
  
  const weekdaysSinceStart = getWeekdaysBetween(START_DATE, date) - 1 // 0-based
  return weekdaysSinceStart % totalArticles
}

const hasArticlesAvailable = computed(() => {
  return currentDate.value >= START_DATE || isDeveloperMode
})

const currentArticle = computed(() => {
  if (!hasArticlesAvailable.value) return null
  const articleIndex = getArticleIndexForDate(currentDate.value)
  return articleIndex !== null ? articles[articleIndex] : null
})

const currentDayNumber = computed(() => {
  const articleIndex = getArticleIndexForDate(currentDate.value)
  return articleIndex !== null ? articleIndex + 1 : 0
})

const daysUntilStart = computed(() => {
  if (hasArticlesAvailable.value) return 0
  
  const today = new Date()
  const startDate = new Date(START_DATE)
  
  // Reset time to start of day for accurate day calculation
  today.setHours(0, 0, 0, 0)
  startDate.setHours(0, 0, 0, 0)
  
  const diffTime = startDate - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  return Math.max(0, diffDays)
})

const countdownText = computed(() => {
  const days = daysUntilStart.value
  if (days === 0) return ''
  if (days === 1) return '1 day to go!'
  return `${days} days to go!`
})

const isWeekendAfterStart = computed(() => {
  const viewingDate = currentDate.value
  const startDate = new Date(START_DATE)
  
  // Check if the date being viewed is after start date and is a weekend
  return viewingDate >= startDate && !isWeekday(viewingDate) && !isDeveloperMode
})

const nextWeekdayDate = computed(() => {
  if (!isWeekendAfterStart.value) return null
  
  // Find the next weekday from the current viewing date
  const nextWeekday = new Date(currentDate.value)
  while (!isWeekday(nextWeekday)) {
    nextWeekday.setDate(nextWeekday.getDate() + 1)
  }
  return nextWeekday
})

const previousButtonText = computed(() => {
  if (isDeveloperMode) {
    return 'Previous'
  } else {
    const prevDate = getPreviousWeekday(currentDate.value)
    const today = new Date()
    const oneWeekAgo = new Date(today)
    oneWeekAgo.setDate(today.getDate() - 7)
    
    // Check if we're at the 1-week limit or start date limit
    if (prevDate < START_DATE || prevDate < oneWeekAgo) {
      return 'Too Old'
    }
    return 'Previous'
  }
})

const canGoToNextDay = computed(() => {
  if (isDeveloperMode) {
    return true // In dev mode, can always navigate
  } else {
    // In production, can only go up to today
    const today = new Date()
    const nextDate = getNextWeekday(currentDate.value)
    return nextDate <= today
  }
})

const canGoToPreviousDay = computed(() => {
  if (isDeveloperMode) {
    return currentDate.value > START_DATE
  } else {
    // Can go back to previous weekday, but not before start date or more than 1 week back
    const prevDate = getPreviousWeekday(currentDate.value)
    const today = new Date()
    const oneWeekAgo = new Date(today)
    oneWeekAgo.setDate(today.getDate() - 7)
    
    return prevDate >= START_DATE && prevDate >= oneWeekAgo
  }
})

// Helper functions to get next/previous weekdays
const getNextWeekday = (date) => {
  const next = new Date(date)
  do {
    next.setDate(next.getDate() + 1)
  } while (!isWeekday(next))
  return next
}

const getPreviousWeekday = (date) => {
  const prev = new Date(date)
  do {
    prev.setDate(prev.getDate() - 1)
  } while (!isWeekday(prev))
  return prev
}

const getNextUnlockDay = () => {
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  
  // Find the next weekday
  while (tomorrow.getDay() === 0 || tomorrow.getDay() === 6) {
    tomorrow.setDate(tomorrow.getDate() + 1)
  }
  
  return tomorrow
}

const nextButtonText = computed(() => {
  if (isDeveloperMode || canGoToNextDay.value) {
    return 'Next'
  } else {
    const nextUnlock = getNextUnlockDay()
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(today.getDate() + 1)
    
    if (nextUnlock.toDateString() === tomorrow.toDateString()) {
      return 'Unlocks Tomorrow'
    } else {
      const dayName = nextUnlock.toLocaleDateString('en-US', { weekday: 'long' })
      return `Unlocks ${dayName}`
    }
  }
})

const nextButtonTooltip = computed(() => {
  if (isDeveloperMode || canGoToNextDay.value) {
    return 'Next Day'
  } else {
    const nextUnlock = getNextUnlockDay()
    return `Next article unlocks on ${nextUnlock.toLocaleDateString('en-US', { 
      weekday: 'long', 
      month: 'short', 
      day: 'numeric' 
    })}`
  }
})

const renderedContent = computed(() => {
  if (!currentArticle.value) return ''
  
  // Configure marked for better formatting
  marked.setOptions({
    breaks: true, // This will convert single \n to <br> tags
    gfm: true,
  })
  
  // Preprocess content to handle custom superscript and subscript syntax
  let processedContent = currentArticle.value.content
  
  // Handle superscript: e^^x^^ -> e<sup>x</sup>
  // Use double carets to avoid conflicts with single caret usage
  processedContent = processedContent.replace(/\^\^([^\^]+)\^\^/g, '<sup>$1</sup>')
  
  // Handle subscript: x,,1,, -> x<sub>1</sub>
  // Use double commas for subscript to avoid conflicts
  processedContent = processedContent.replace(/,,([^,]+),,/g, '<sub>$1</sub>')
  
  return marked(processedContent)
})

const estimatedReadingTime = computed(() => {
  if (!currentArticle.value) return ''
  
  // Count words in the content (simple word count by splitting on whitespace)
  const words = currentArticle.value.content.trim().split(/\s+/).length
  
  // Average reading speed is about 200 words per minute
  const averageWordsPerMinute = 200
  const minutes = Math.ceil(words / averageWordsPerMinute)
  
  // Return formatted string
  if (minutes === 1) {
    return '1 minute read'
  } else {
    return `${minutes} minute read`
  }
})

const formatDate = (date) => {
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const goToPreviousDay = () => {
  if (canGoToPreviousDay.value) {
    currentDate.value = getPreviousWeekday(currentDate.value)
    scrollToTop()
  }
}

const goToNextDay = () => {
  if (canGoToNextDay.value) {
    currentDate.value = getNextWeekday(currentDate.value)
    scrollToTop()
  }
}

const goToToday = () => {
  currentDate.value = new Date()
  // If today is not a weekday, find the most recent weekday
  if (!isWeekday(currentDate.value)) {
    currentDate.value = getPreviousWeekday(currentDate.value)
  }
  scrollToTop()
}

// Developer mode: Select article by index
const selectArticle = (event) => {
  if (!isDeveloperMode) return
  
  const articleIndex = parseInt(event.target.value)
  
  // Calculate the date for this article index
  // Start from START_DATE and add weekdays to reach the desired article
  let targetDate = new Date(START_DATE)
  
  for (let i = 0; i < articleIndex; i++) {
    targetDate = getNextWeekday(targetDate)
  }
  
  currentDate.value = targetDate
  scrollToTop()
}

// Share functionality
const shareArticle = async () => {
  if (!currentArticle.value) return
  
  const pageUrl = window.location.href
  const today = new Date()
  const isToday = currentDate.value.toDateString() === today.toDateString()
  
  let shareMessage
  if (isToday) {
    shareMessage = `Today's Daily Architect Wisdom: ${currentArticle.value.title} - ${pageUrl}`
  } else {
    shareMessage = `Daily Architect Wisdom - ${pageUrl}`
  }
  
  try {
    await navigator.clipboard.writeText(shareMessage)
    showToastNotification()
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
    // Fallback for older browsers
    const success = fallbackCopyTextToClipboard(shareMessage)
    if (success) {
      showToastNotification()
    }
  }
}

// Show toast notification
const showToastNotification = () => {
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000) // Hide after 3 seconds
}

// Fallback copy function for older browsers
const fallbackCopyTextToClipboard = (text) => {
  const textArea = document.createElement('textarea')
  textArea.value = text
  
  // Avoid scrolling to bottom
  textArea.style.top = '0'
  textArea.style.left = '0'
  textArea.style.position = 'fixed'
  
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  
  try {
    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    return successful
  } catch (err) {
    console.error('Fallback: Unable to copy to clipboard', err)
    document.body.removeChild(textArea)
    return false
  }
}


// Scroll handling for header minimization with hysteresis to prevent jittering
const handleScroll = () => {
  const currentScrollY = window.scrollY
  
  // Use different thresholds for scrolling down vs up to prevent jittery behavior
  const SCROLL_DOWN_THRESHOLD = 200
  const SCROLL_UP_THRESHOLD = 50
  
  if (currentScrollY > lastScrollY.value) {
    // Scrolling down
    if (currentScrollY > SCROLL_DOWN_THRESHOLD) {
      isScrolled.value = true
    }
  } else {
    // Scrolling up
    if (currentScrollY < SCROLL_UP_THRESHOLD) {
      isScrolled.value = false
    }
  }
  
  lastScrollY.value = currentScrollY
}

// Smooth scroll to top
const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'instant'
  })
}

// Mobile detection
const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('resize', handleResize)
  handleResize() // Initial check
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.daily-inspiration {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
  position: relative;
}

/* Toast notification styles */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #10b981, #34d399);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.4);
  transform: translateX(100%);
  opacity: 0;
  transition: all 0.3s ease;
  z-index: 1000;
}

.toast-show {
  transform: translateX(0);
  opacity: 1;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 2rem;
}

.header {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 2rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.3s ease;
}

.header-minimized {
  padding: 1rem 0;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(15px);
}

.header-minimized .title {
  font-size: 1.8rem;
  margin-bottom: 0;
}

.title {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #10b981, #34d399);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
  transition: all 0.3s ease;
}

.date-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  transition: all 0.3s ease;
  margin-bottom: 1rem;
}

.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.header-navigation {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.share-button {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);
}

.share-button:hover {
  background: linear-gradient(135deg, #d97706, #ea580c);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(245, 158, 11, 0.4);
}

.dev-selector {
  margin-right: 1rem;
}

.article-selector {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e5e7eb;
  padding: 0.5rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.article-selector:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

.article-selector:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.2);
  border-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
}

.article-selector option {
  background: #1a1a1a;
  color: #e5e7eb;
  padding: 0.5rem;
}

.nav-button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e5e7eb;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  white-space: nowrap;
  min-width: fit-content;
}

.nav-button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.nav-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-button.today {
  background: linear-gradient(135deg, #10b981, #34d399);
  border: none;
  color: #000;
  font-weight: 600;
}

.nav-button.today:hover {
  background: linear-gradient(135deg, #059669, #10b981);
  transform: translateY(-2px);
}

.current-date {
  font-size: 1.125rem;
  color: #d1d5db;
}

.day-counter {
  font-size: 0.875rem;
  color: #9ca3af;
  background: rgba(255, 255, 255, 0.1);
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
}

.main-content {
  padding: 3rem 0;
}

.no-articles {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.no-articles-content {
  text-align: center;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 3rem 2rem;
  max-width: 500px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
}

.no-articles-title {
  font-size: 2.5rem;
  font-weight: 600;
  background: linear-gradient(135deg, #10b981, #34d399);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1.5rem;
}

.no-articles-message {
  font-size: 1.125rem;
  color: #e5e7eb;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.no-articles-subtitle {
  font-size: 1rem;
  color: #9ca3af;
  font-style: italic;
}

.countdown {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 2rem 0;
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(52, 211, 153, 0.1));
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.countdown-number {
  font-size: 4rem;
  font-weight: 700;
  background: linear-gradient(135deg, #10b981, #34d399);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.countdown-label {
  font-size: 1.25rem;
  font-weight: 600;
  color: #e5e7eb;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Weekend Message Styles */
.weekend-message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.weekend-content {
  text-align: center;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 3rem 2rem;
  max-width: 500px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.05), rgba(249, 115, 22, 0.05));
  border-color: rgba(245, 158, 11, 0.2);
}

.weekend-title {
  font-size: 2.5rem;
  font-weight: 600;
  background: linear-gradient(135deg, #f59e0b, #f97316);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1.5rem;
}

.weekend-text {
  font-size: 1.125rem;
  color: #e5e7eb;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.weekend-subtitle {
  font-size: 1rem;
  color: #9ca3af;
  font-style: italic;
}

/* Footer Styles */
.footer {
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: 4rem;
}

.footer-content {
  text-align: center;
  padding: 2rem 0;
}

.attribution {
  font-size: 1rem;
  color: #e5e7eb;
  margin-bottom: 0.5rem;
}

.attribution strong {
  color: #10b981;
  font-weight: 600;
}

.purchase-link {
  margin: 1rem 0;
}

.book-link {
  display: inline-block;
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: white;
  text-decoration: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.book-link:hover {
  background: linear-gradient(135deg, #047857 0%, #065f46 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.2);
}

.credit {
  font-size: 0.875rem;
  color: #9ca3af;
  font-style: italic;
  margin-top: 0.5rem;
}

.article {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 2.5rem;
  margin-bottom: 3rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
}

.article-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.article-title {
  font-size: 2rem;
  font-weight: 600;
  color: #f9fafb;
  margin-bottom: 0.5rem;
  line-height: 1.2;
}

.article-author {
  font-size: 1rem;
  color: #9ca3af;
  font-style: italic;
}

.article-reading-time {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
}

.article-reading-time::before {
  content: '⏳';
  margin-right: 0.5rem;
}

.article-content {
  font-size: 1.125rem;
  line-height: 1.8;
  color: #e5e7eb;
}

/* Markdown content styling */
.article-content :deep(p) {
  margin-bottom: 2rem;
}

.article-content :deep(p:last-child) {
  margin-bottom: 0;
}

.article-content :deep(br) {
  display: block;
  margin: 1.5rem 0;
  content: "";
}

.article-content :deep(ul) {
  margin: 2rem 0;
  padding-left: 2rem;
}

.article-content :deep(ol) {
  margin: 2rem 0;
  padding-left: 2rem;
}

.article-content :deep(li) {
  margin-bottom: 1rem;
  line-height: 1.8;
}

.article-content :deep(li:last-child) {
  margin-bottom: 0;
}

.article-content :deep(strong) {
  color: #f9fafb;
  font-weight: 600;
}

.article-content :deep(em) {
  color: #d1d5db;
}

.article-content :deep(sup) {
  color: #10b981;
  font-size: 0.75em;
  vertical-align: super;
  line-height: 0;
}

.article-content :deep(sub) {
  color: #34d399;
  font-size: 0.75em;
  vertical-align: sub;
  line-height: 0;
}

.article-content :deep(a) {
  color: #10b981;
  text-decoration: none;
  border-bottom: 1px solid rgba(16, 185, 129, 0.3);
  transition: all 0.2s ease;
  font-weight: 500;
}

.article-content :deep(a:hover) {
  color: #34d399;
  border-bottom-color: rgba(52, 211, 153, 0.6);
  background: rgba(16, 185, 129, 0.1);
  padding: 0.125rem 0.25rem;
  margin: -0.125rem -0.25rem;
  border-radius: 0.25rem;
}

.article-content :deep(a:visited) {
  color: #fbbf24;
  border-bottom-color: rgba(251, 191, 36, 0.3);
}

.article-content :deep(a:visited:hover) {
  color: #fcd34d;
  border-bottom-color: rgba(252, 211, 77, 0.6);
  background: rgba(251, 191, 36, 0.1);
}

/* Table styles */
.article-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 2rem 0;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.article-content :deep(thead) {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(52, 211, 153, 0.1));
  border-bottom: 2px solid rgba(16, 185, 129, 0.3);
}

.article-content :deep(th) {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #f9fafb;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.article-content :deep(th:last-child) {
  border-right: none;
}

.article-content :deep(td) {
  padding: 0.875rem 1rem;
  color: #e5e7eb;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.9rem;
  line-height: 1.5;
}

.article-content :deep(td:last-child) {
  border-right: none;
}

.article-content :deep(tbody tr:last-child td) {
  border-bottom: none;
}

.article-content :deep(tbody tr:hover) {
  background: rgba(255, 255, 255, 0.03);
}

.article-content :deep(tbody tr:nth-child(even)) {
  background: rgba(255, 255, 255, 0.01);
}

.article-content :deep(tbody tr:nth-child(even):hover) {
  background: rgba(255, 255, 255, 0.04);
}

.article-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: 'Fira Code', 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.9em;
  color: #fbbf24;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.article-content :deep(pre) {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin: 2rem 0;
  overflow-x: auto;
  font-family: 'Fira Code', 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #e5e7eb;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

.article-content :deep(pre code) {
  background: none;
  padding: 0;
  border: none;
  border-radius: 0;
  font-size: inherit;
  color: inherit;
  display: block;
}

/* Syntax highlighting for common keywords */
.article-content :deep(pre code) {
  white-space: pre;
  word-wrap: normal;
}

.article-content :deep(blockquote) {
  border-left: 3px solid #10b981;
  padding-left: 1.5rem;
  margin: 2rem 0;
  font-style: italic;
  color: #d1d5db;
}

/* Responsive design */
@media (max-width: 768px) {
  .container {
    padding: 0 1rem;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .header-minimized .title {
    font-size: 1.5rem;
  }
  
  .article {
    padding: 1.5rem;
  }
  
  .article-title {
    font-size: 1.5rem;
  }
  
  .article-content {
    font-size: 1rem;
  }
  
  /* Mobile code block styles */
  .article-content :deep(pre) {
    padding: 1rem;
    margin: 1.5rem 0;
    font-size: 0.8rem;
    border-radius: 0.375rem;
  }
  
  .article-content :deep(code) {
    font-size: 0.85em;
    padding: 0.1rem 0.3rem;
  }
  
  .article-content :deep(a:hover) {
    padding: 0.1rem 0.2rem;
    margin: -0.1rem -0.2rem;
  }
  
  /* Mobile table styles */
  .article-content :deep(table) {
    font-size: 0.8rem;
    margin: 1.5rem 0;
  }
  
  .article-content :deep(th) {
    padding: 0.75rem 0.5rem;
    font-size: 0.75rem;
  }
  
  .article-content :deep(td) {
    padding: 0.6rem 0.5rem;
    font-size: 0.8rem;
  }
  
  /* Enable horizontal scrolling for wide tables on mobile */
  .article-content :deep(table) {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }
  
  .article-content :deep(thead),
  .article-content :deep(tbody),
  .article-content :deep(tr) {
    display: table;
    width: 100%;
    table-layout: fixed;
  }
  
  .date-info {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-controls {
    flex-direction: row;
    gap: 0.5rem;
    align-items: center;
    justify-content: space-between;
  }
  
  /* Add spacing for collapsed header on mobile */
  .header-minimized .header-controls {
    margin-top: 1rem;
  }
  
  .header-navigation {
    justify-content: flex-start;
    gap: 0.25rem;
    flex: 1;
  }
  
  .header-actions {
    justify-content: flex-end;
    flex-shrink: 0;
  }
  
  .share-button {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
  }
  
  .dev-selector {
    margin-right: 0.5rem;
  }
  
  .article-selector {
    padding: 0.375rem 0.5rem;
    font-size: 0.75rem;
    max-width: 200px;
  }
  
  .nav-button {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
  }
  
  .toast {
    top: 10px;
    right: 10px;
    left: 10px;
    font-size: 0.8rem;
    padding: 0.6rem 1rem;
  }
  
  .no-articles-content {
    padding: 2rem 1.5rem;
    margin: 0 1rem;
  }
  
  .no-articles-title {
    font-size: 2rem;
  }
  
  .countdown {
    margin: 1.5rem 0;
    padding: 1rem;
  }
  
  .countdown-number {
    font-size: 3rem;
  }
  
  .countdown-label {
    font-size: 1rem;
  }
  
  .weekend-content {
    padding: 2rem 1.5rem;
    margin: 0 1rem;
  }
  
  .weekend-title {
    font-size: 2rem;
  }
  
  .footer-content {
    text-align: center;
    padding: 1rem 0;
  }
  
  .attribution {
    font-size: 0.9rem;
  }
  
  .purchase-link {
    margin: 0.5rem 0;
  }
  
  .book-link {
    font-size: 0.9rem;
    padding: 0.4rem 0.8rem;
  }
  
  .credit {
    font-size: 0.8rem;
  }
}
</style>
