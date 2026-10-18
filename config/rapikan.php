<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Python Analysis Engine Configuration
    |--------------------------------------------------------------------------
    | Path to the Python executable in the virtual environment.
    */
    'python_path' => env('RAPIKAN_PYTHON_PATH', base_path('python/.venv/Scripts/python.exe')),

    /*
    | Root directory for uploaded documents (shared volume with Python).
    | Python strictly rejects paths outside this directory.
    */
    'documents_disk' => 'documents',
    'documents_base_dir' => storage_path('app/documents'),

    /*
    | Security & File Limits
    */
    'max_file_size_mb' => (int) env('RAPIKAN_MAX_FILE_SIZE_MB', 50),
    'max_zip_entries' => 1000,
    'max_zip_ratio' => 100,

    /*
    | Retention Policy (in days)
    */
    'document_ttl_days' => (int) env('RAPIKAN_DOCUMENT_TTL_DAYS', 30),

    /*
    | Campus Profile
    */
    'default_profile' => env('RAPIKAN_DEFAULT_PROFILE', 'default'),

    /*
    | LLM Configuration (Disabled until Phase 4)
    */
    'llm_enabled' => false,
];
