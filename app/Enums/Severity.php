<?php

namespace App\Enums;

enum Severity: string
{
    case ERROR = 'error';
    case WARNING = 'warning';
    case INFO = 'info';

    public function label(): string
    {
        return match ($this) {
            self::ERROR => 'Kesalahan (Error)',
            self::WARNING => 'Peringatan (Warning)',
            self::INFO => 'Informasi (Info)',
        };
    }

    public function badgeClass(): string
    {
        return match ($this) {
            self::ERROR => 'bg-red-100 text-red-800 border-red-300',
            self::WARNING => 'bg-yellow-100 text-yellow-800 border-yellow-300',
            self::INFO => 'bg-blue-100 text-blue-800 border-blue-300',
        };
    }
}
