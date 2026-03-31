<script setup>
import { ref, computed, onMounted } from 'vue'
import { cpqApi } from '../../api/cpq'

const products = ref([])
const families = ref([])
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')
const selectedFamily = ref('')

const filteredProducts = computed(() => {
  let result = products.value
  if (selectedFamily.value) {
    result = result.filter((p) => p.family === selectedFamily.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.family.toLowerCase().includes(q),
    )
  }
  return result
})

const groupedProducts = computed(() => {
  const groups = {}
  for (const product of filteredProducts.value) {
    if (!groups[product.family]) groups[product.family] = []
    groups[product.family].push(product)
  }
  return groups
})

function formatPrice(product) {
  if (product.unit_price === 0) return 'Free'
  return `$${product.unit_price % 1 === 0 ? product.unit_price : product.unit_price.toFixed(2)}`
}

async function fetchProducts() {
  loading.value = true
  error.value = null
  try {
    const res = await cpqApi.getProducts()
    products.value = res.data.products
    families.value = res.data.families
  } catch (e) {
    error.value = e.message || 'Failed to load products'
  } finally {
    loading.value = false
  }
}

onMounted(fetchProducts)
</script>

<template>
  <div>
    <!-- Search & filter bar -->
    <div class="flex flex-col sm:flex-row gap-3 mb-6">
      <div class="relative flex-1">
        <svg
          class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[--color-text-muted]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" stroke-linecap="round" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search products..."
          class="w-full pl-10 pr-3 py-2 text-sm bg-[--color-surface] border border-[--color-border] rounded-lg text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] focus:ring-1 focus:ring-[--color-primary] transition-colors"
        />
      </div>
      <div class="flex gap-2 flex-wrap">
        <button
          :class="[
            'px-3 py-1.5 text-xs font-semibold rounded-full border transition-colors cursor-pointer',
            !selectedFamily
              ? 'bg-[--color-primary] text-white border-[--color-primary]'
              : 'bg-[--color-surface] text-[--color-text-secondary] border-[--color-border] hover:border-[--color-primary] hover:text-[--color-primary]',
          ]"
          @click="selectedFamily = ''"
        >
          All
        </button>
        <button
          v-for="family in families"
          :key="family"
          :class="[
            'px-3 py-1.5 text-xs font-semibold rounded-full border transition-colors cursor-pointer',
            selectedFamily === family
              ? 'bg-[--color-primary] text-white border-[--color-primary]'
              : 'bg-[--color-surface] text-[--color-text-secondary] border-[--color-border] hover:border-[--color-primary] hover:text-[--color-primary]',
          ]"
          @click="selectedFamily = family"
        >
          {{ family }}
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="n in 6"
        :key="n"
        class="h-56 rounded-lg bg-[--color-border] animate-pulse"
      />
    </div>

    <!-- Error state -->
    <div
      v-else-if="error"
      class="text-center py-12 text-[--color-text-secondary]"
    >
      <p class="text-sm mb-3">{{ error }}</p>
      <button
        class="text-sm font-semibold text-[--color-primary] hover:underline cursor-pointer"
        @click="fetchProducts"
      >
        Retry
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="filteredProducts.length === 0"
      class="text-center py-12 text-[--color-text-muted] text-sm"
    >
      No products match your search.
    </div>

    <!-- Product grid grouped by family -->
    <div v-else class="space-y-8">
      <section v-for="(items, family) in groupedProducts" :key="family">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-[--color-text-muted] mb-3">
          {{ family }}
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="product in items"
            :key="product.id"
            :class="[
              'relative bg-[--color-surface] border rounded-lg p-5 transition-shadow hover:shadow-md',
              product.popular
                ? 'border-[--color-primary] ring-1 ring-[--color-primary]'
                : 'border-[--color-border]',
            ]"
          >
            <!-- Most Popular ribbon -->
            <span
              v-if="product.popular"
              class="absolute -top-2.5 left-4 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide bg-[--color-primary] text-white rounded-full"
            >
              Most Popular
            </span>

            <!-- Family badge -->
            <span
              class="inline-block px-2 py-0.5 text-[10px] font-semibold rounded-full bg-[--color-primary-light] text-[--color-primary] mb-3"
            >
              {{ product.family }}
            </span>

            <!-- Name -->
            <h4 class="text-base font-semibold text-[--color-text] mb-1">
              {{ product.name }}
            </h4>

            <!-- Price -->
            <div class="mb-3">
              <span class="text-2xl font-bold text-[--color-primary]">
                {{ formatPrice(product) }}
              </span>
              <span
                v-if="product.unit_price > 0"
                class="text-xs text-[--color-text-muted] ml-1"
              >
                {{ product.billing_frequency }}
              </span>
            </div>

            <!-- Description -->
            <p class="text-xs text-[--color-text-secondary] leading-relaxed mb-4">
              {{ product.description }}
            </p>

            <!-- Features -->
            <ul class="space-y-1">
              <li
                v-for="feature in product.features"
                :key="feature"
                class="flex items-center gap-1.5 text-xs text-[--color-text-secondary]"
              >
                <svg class="w-3.5 h-3.5 text-[--color-success] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                {{ feature }}
              </li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
