<?php

namespace App\Enums;

enum FileType: string
{
    case DOCX = 'docx';
    case XLSX = 'xlsx';
    case PDF = 'pdf';
    case GDOCS = 'gdocs';
    case GSHEETS = 'gsheets';
    case GFORMS = 'gforms';

    public function label(): string
    {
        return match ($this) {
            self::DOCX => 'Microsoft Word (.docx)',
            self::XLSX => 'Microsoft Excel (.xlsx)',
            self::PDF => 'PDF (.pdf)',
            self::GDOCS => 'Google Docs',
            self::GSHEETS => 'Google Sheets',
            self::GFORMS => 'Google Forms',
        };
    }
}
