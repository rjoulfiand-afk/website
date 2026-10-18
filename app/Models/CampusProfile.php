<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class CampusProfile extends Model
{
    use HasFactory, HasUuids;

    protected $fillable = [
        'slug',
        'name',
        'version',
        'source_document',
        'guideline_year',
        'verified',
        'rules_yaml',
        'config',
        'is_active',
    ];

    protected $casts = [
        'verified' => 'boolean',
        'is_active' => 'boolean',
        'config' => 'array',
        'guideline_year' => 'integer',
    ];

    public function documents(): HasMany
    {
        return $this->hasMany(Document::class);
    }
}
