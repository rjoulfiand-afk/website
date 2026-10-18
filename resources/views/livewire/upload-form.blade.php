<div class="max-w-2xl mx-auto">
    <!-- Header Hero -->
    <div class="text-center mb-8">
        <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight sm:text-4xl">
            Periksa Kerapian Naskah Anda
        </h1>
        <p class="mt-2 text-base text-gray-600">
            Unggah dokumen (.docx) skripsi atau laporan ilmiah untuk mendeteksi ketidaksesuaian gaya heading, penomoran, margin, spasi, dan rujukan secara otomatis.
        </p>
    </div>

    <!-- Upload Card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8">
        @if ($errorMessage)
            <div class="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 flex items-start space-x-3">
                <svg class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                    <h4 class="font-semibold text-red-800">Gagal Mengunggah Berkas</h4>
                    <p class="mt-1">{{ $errorMessage }}</p>
                </div>
            </div>
        @endif

        <form wire:submit="processUpload" class="space-y-6">
            <!-- File Input Area -->
            <div>
                <label class="block text-sm font-semibold text-gray-800 mb-2">
                    Pilih Berkas Dokumen (.docx)
                </label>
                <div 
                    x-data="{ isDropping: false }"
                    @dragover.prevent="isDropping = true"
                    @dragleave.prevent="isDropping = false"
                    @drop.prevent="isDropping = false"
                    :class="{ 'border-blue-500 bg-blue-50/50': isDropping, 'border-gray-300 hover:border-gray-400': !isDropping }"
                    class="relative border-2 border-dashed rounded-lg p-8 text-center transition cursor-pointer"
                >
                    <input 
                        type="file" 
                        wire:model="file" 
                        id="document-upload" 
                        accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    >

                    <div class="space-y-2">
                        <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                            <path d="M28 8H12a4 4 0 00-4 4v24a4 4 0 004 4h24a4 4 0 004-4V20L28 8z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                            <path d="M28 8v12h12M16 26h16M16 34h10" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>

                        <div class="text-sm text-gray-600">
                            @if ($file)
                                <span class="font-semibold text-blue-600">{{ $file->getClientOriginalName() }}</span>
                                <span class="text-xs text-gray-500 block mt-1">({{ round($file->getSize() / 1024, 1) }} KB)</span>
                            @else
                                <span class="font-medium text-blue-600 hover:underline">Klik untuk telusuri</span> atau seret berkas ke sini
                            @endif
                        </div>
                        <p class="text-xs text-gray-500">Maksimum ukuran berkas: {{ $maxSizeMb }} MB</p>
                    </div>
                </div>

                @error('file')
                    <p class="mt-1.5 text-xs text-red-600">{{ $message }}</p>
                @enderror

                <!-- Uploading state indicator -->
                <div wire:loading wire:target="file" class="mt-2 text-xs text-blue-600 flex items-center space-x-2">
                    <svg class="animate-spin h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                    </svg>
                    <span>Mengunggah berkas ke server sementara...</span>
                </div>
            </div>

            <!-- Campus Profile Selection -->
            <div>
                <label for="campus-profile" class="block text-sm font-semibold text-gray-800 mb-1">
                    Profil Aturan Format
                </label>
                <select 
                    wire:model="campusProfileId" 
                    id="campus-profile" 
                    class="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm py-2 px-3 border"
                >
                    <option value="">Pedoman Standar (Default Umum)</option>
                    @foreach ($profiles as $profile)
                        <option value="{{ $profile->id }}">
                            {{ $profile->name }} (v{{ $profile->version }})
                            @if (!$profile->verified) [Belum Terverifikasi] @endif
                        </option>
                    @endforeach
                </select>
                <p class="mt-1 text-xs text-gray-500">
                    Menentukan batas ukuran font heading, margin seksi, pola penomoran, dan urutan bab.
                </p>
            </div>

            <!-- Genre / Blueprint Selection -->
            <div>
                <label for="doc-genre" class="block text-sm font-semibold text-gray-800 mb-1">
                    Jenis Naskah / Dokumen (Genre)
                </label>
                <select 
                    wire:model="genre" 
                    id="doc-genre" 
                    class="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm py-2 px-3 border bg-white"
                >
                    @foreach ($genres as $g)
                        <option value="{{ $g->value }}">
                            {{ $g->label() }}
                        </option>
                    @endforeach
                </select>
                <p class="mt-1 text-xs text-gray-500">
                    Memilih struktur bab dan acuan susunan yang dievaluasi (mis. Skripsi Bab I-V, Proposal Bab I-III, atau Makalah ringkas).
                </p>
            </div>

            <!-- Privacy & Security Notice -->
            <div class="rounded-lg bg-gray-50 border border-gray-200 p-4 space-y-3">
                <div class="flex items-start space-x-2 text-xs text-gray-600">
                    <svg class="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span><strong>Keamanan Berkas:</strong> Berkas Anda disimpan di ruang privat terenkripsi hash, tidak dapat diakses publik, dan otomatis dihapus setelah 30 hari. Berkas asli tidak pernah ditimpa.</span>
                </div>

                <div class="flex items-center space-x-2">
                    <input 
                        type="checkbox" 
                        wire:model="llmConsent" 
                        id="llm-consent" 
                        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                    >
                    <label for="llm-consent" class="text-xs text-gray-600">
                        Saya menyetujui teks dievaluasi dengan AI / model semantik bila diperlukan (Fase 1-3 murni berjalan secara deterministik tanpa LLM).
                    </label>
                </div>
            </div>

            <!-- Submit Button -->
            <div>
                <button 
                    type="submit" 
                    wire:loading.attr="disabled"
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg shadow-sm transition flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                    <span wire:loading.remove wire:target="processUpload">Mulai Analisis Dokumen</span>
                    <span wire:loading wire:target="processUpload" class="flex items-center space-x-2">
                        <svg class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                        </svg>
                        <span>Menganalisis Naskah...</span>
                    </span>
                </button>
            </div>
        </form>
    </div>
</div>
