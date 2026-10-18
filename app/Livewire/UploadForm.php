<?php

namespace App\Livewire;

use App\Enums\DocumentGenre;
use App\Enums\JobStatus;
use App\Jobs\DispatchAnalysis;
use App\Models\CampusProfile;
use App\Models\Document;
use App\Services\FileTypeDetector;
use Exception;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Livewire\Component;
use Livewire\WithFileUploads;

class UploadForm extends Component
{
    use WithFileUploads;

    public $file;
    public ?string $campusProfileId = null;
    public string $genre = 'auto';
    public bool $llmConsent = false;
    public ?string $errorMessage = null;
    public bool $isUploading = false;

    public function mount(): void
    {
        // Default to active default profile if exists
        $default = CampusProfile::where('slug', config('rapikan.default_profile', 'default'))->first();
        if ($default) {
            $this->campusProfileId = $default->id;
        }
    }

    public function rules(): array
    {
        $maxBytes = config('rapikan.max_file_size_mb', 50) * 1024;
        return [
            'file' => ['required', 'file', "max:{$maxBytes}"],
            'campusProfileId' => ['nullable', 'exists:campus_profiles,id'],
            'genre' => ['required', 'string'],
            'llmConsent' => ['boolean'],
        ];
    }

    public function processUpload(FileTypeDetector $detector)
    {
        $this->errorMessage = null;
        $this->validate();

        try {
            $tempPath = $this->file->getRealPath();

            // 1. Content-based detection (magic bytes)
            $detection = $detector->detect($tempPath);

            // 2. Hash and UUID file path
            $fileHash = hash_file('sha256', $tempPath);
            $fileSize = filesize($tempPath);
            $uuid = (string) Str::uuid();
            $ext = $detection['file_type']->value;
            $storageFilename = "raw/{$uuid}.{$ext}";

            // 3. Store file into private 'documents' disk
            $stream = fopen($tempPath, 'r+');
            Storage::disk('documents')->put($storageFilename, $stream);
            if (is_resource($stream)) {
                fclose($stream);
            }

            // 4. Create Document record
            $document = Document::create([
                'user_id' => auth()->id(),
                'original_filename' => $this->file->getClientOriginalName(),
                'file_type' => $detection['file_type'],
                'detection_confidence' => $detection['confidence'],
                'storage_path' => $storageFilename,
                'file_hash' => $fileHash,
                'file_size_bytes' => $fileSize,
                'campus_profile_id' => $this->campusProfileId,
                'genre' => DocumentGenre::tryFrom($this->genre) ?? DocumentGenre::AUTO,
                'status' => JobStatus::QUEUED,
                'llm_consent_given' => $this->llmConsent,
                'expires_at' => now()->addDays(config('rapikan.document_ttl_days', 30)),
            ]);

            // 5. Dispatch Analysis Job (run synchronously if sync queue, or queued)
            DispatchAnalysis::dispatch($document);

            // 6. Redirect to report page
            return redirect()->route('report.show', $document->id);

        } catch (Exception $e) {
            $this->errorMessage = $e->getMessage();
        }
    }

    public function render()
    {
        $profiles = CampusProfile::where('is_active', true)->get();

        return view('livewire.upload-form', [
            'profiles' => $profiles,
            'genres' => DocumentGenre::cases(),
            'maxSizeMb' => config('rapikan.max_file_size_mb', 50),
        ]);
    }
}
