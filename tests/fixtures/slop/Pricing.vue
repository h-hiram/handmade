<template>
  <section class="py-24 text-center">
    <h2 class="text-[42px] font-bold">Everything you need to scale</h2>
    <div class="grid md:grid-cols-3 gap-8 mt-12">
      <div v-for="plan in plans" :key="plan.name" :class="['rounded-3xl shadow-2xl p-8', plan.featured ? 'bg-indigo-600 text-white' : 'bg-white']">
        <h3 class="text-xl">{{ plan.name }}</h3>
        <button class="mt-6 rounded-full bg-indigo-600 px-4 py-2 text-white transition-all hover:scale-105">Choose</button>
      </div>
    </div>
  </section>
</template>

<script setup>
const plans = [
  { name: 'Starter', blurb: 'Unlock powerful features for your team' },
  { name: 'Pro', blurb: 'Take your business to the next level' },
]
</script>

<style scoped>
section { animation: fade 1s ease; }
</style>
