<?php

namespace App\Enums;

enum JobStatus: string
{
    case QUEUED = 'queued';
    case PROCESSING = 'processing';
    case DONE = 'done';
    case FAILED = 'failed';

    public function label(): string
    {
        return match ($this) {
            self::QUEUED => 'Dalam Antrean',
            self::PROCESSING => 'Sedang Dianalisis',
            self::DONE => 'Selesai',
            self::FAILED => 'Gagal',
        };
    }
}
