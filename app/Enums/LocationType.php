<?php

namespace App\Enums;

enum LocationType: string
{
    case PARAGRAPH = 'paragraph';
    case SECTION = 'section';
    case CELL = 'cell';
    case TABLE = 'table';
    case IMAGE = 'image';
    case FOOTER = 'footer';
    case DOCUMENT = 'document';

    public function label(): string
    {
        return match ($this) {
            self::PARAGRAPH => 'Paragraf',
            self::SECTION => 'Seksi / Halaman',
            self::CELL => 'Sel Tabel / Sheet',
            self::TABLE => 'Tabel',
            self::IMAGE => 'Gambar',
            self::FOOTER => 'Header / Footer',
            self::DOCUMENT => 'Dokumen Keseluruhan',
        };
    }
}
