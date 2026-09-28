<x-modal name="logout-modal" title="Logout">
    <form class="space-y-4 text-lg" action="{{ route('logout') }}" method="post">
        @csrf
        <p>
            Are you sure that you want to log out?
        </p>
        <div class="flex justify-end gap-x-5">
            <button class="cursor-pointer" type="button" @click="$dispatch('close-modal')">Cancel</button>
            <button type="submit" class="cursor-pointer inline-flex items-center justify-center whitespace-nowrap rounded-full bg-caa-green px-5 py-3 text-center text-white transition hover:bg-caa-forest">Logout</button>
        </div>
    </form>
</x-modal>
