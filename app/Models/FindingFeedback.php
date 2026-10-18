<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class FindingFeedback extends Model
{
    use HasFactory, HasUuids;

    protected $table = 'finding_feedback';

    protected $fillable = [
        'finding_id',
        'user_id',
        'is_false_positive',
        'reason',
    ];

    protected $casts = [
        'is_false_positive' => 'boolean',
    ];

    public function finding(): BelongsTo
    {
        return $this->belongsTo(Finding::class);
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
