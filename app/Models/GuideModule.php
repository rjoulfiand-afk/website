<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class GuideModule extends Model
{
    use HasFactory, HasUuids;

    protected $fillable = [
        'slug',
        'app_target',
        'title',
        'definition',
        'when_to_use',
        'how_to_use',
        'how_to_remove',
        'how_to_fix',
        'common_mistakes',
        'example_before',
        'example_after',
        'app_version_verified',
        'verified_at',
        'is_published',
    ];

    protected $casts = [
        'verified_at' => 'date',
        'is_published' => 'boolean',
    ];

    public function findings(): HasMany
    {
        return $this->hasMany(Finding::class);
    }
}
