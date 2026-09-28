@props(['name', 'title'])

<div
    x-data="{ show: false, name: @js($name) }"
    x-show="show"
    @open-modal.window="if($event.detail === name) show = true"
    @close-modal="show = false"
    @keydown.escape.window="show = false"
    x-transition:enter="transition-opacity ease-out duration-200"
    x-transition:enter-start="opacity-0"
    x-transition:enter-end="opacity-100"
    x-transition:leave="transition-opacity ease-in duration-150"
    x-transition:leave-start="opacity-100"
    x-transition:leave-end="opacity-0"
    class="fixed inset-0 z-50 grid place-items-center overflow-y-auto p-4 sm:p-6"
    style="display: none"
>
    <div
        class="absolute inset-0 bg-slate-950/50 backdrop-blur-sm dark:bg-black/65"
        @click="show = false"
        aria-hidden="true"
    ></div>

    <div
        @click.stop
        class="relative z-10 max-h-[80dvh] w-full max-w-lg overflow-y-auto rounded-2xl border border-gray-200 bg-white p-6 text-gray-900 shadow-2xl shadow-slate-950/20 sm:p-8 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-{{ $name }}-title"
        :aria-hidden="!show"
        tabindex="-1"
    >
        <div class="flex items-start justify-between gap-4 border-b border-gray-200 pb-4 dark:border-slate-700">
            <h2 id="modal-{{ $name }}-title" class="text-xl font-semibold tracking-tight text-gray-900 dark:text-slate-100">{{ $title }}</h2>

            <button
                @click="show = false"
                class="cursor-pointer rounded-full p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--sea-primary)] dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white"
                type="button"
                aria-label="Close modal"
            >
                <x-icons.close />
            </button>
        </div>

        <div class="pt-5">
            {{ $slot }}
        </div>
    </div>
</div>
