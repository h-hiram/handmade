@extends('layouts.app')

@section('content')
<div class="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500">
  <div class="mx-auto max-w-3xl py-24 text-center">
    <h1 class="text-5xl font-bold text-white">Welcome to {{ config('app.name') }}</h1>
    <p class="mt-4 text-white/80">Revolutionize the way your team works.</p>
    <a href="{{ route('register') }}" class="rounded-xl bg-white px-6 py-3 text-indigo-600 shadow-lg">Start free</a>
    <a href="{{ route('login') }}" class="rounded-xl px-6 py-3 text-white">Sign in</a>
  </div>
  <div @class(['rounded-2xl', 'bg-white/10', 'backdrop-blur-lg', 'p-6' => $padded])>
    🎉 You're all set!
  </div>
</div>
@endsection
