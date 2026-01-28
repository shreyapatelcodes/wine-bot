/**
 * Skeleton loading state for wine cards
 */

export function WineCardSkeleton() {
  return (
    <div className="bg-white/50 border border-wine-600/10 rounded-xl p-5 animate-pulse">
      <div className="flex gap-4">
        {/* Wine image placeholder */}
        <div className="w-16 h-24 bg-gray-200 rounded-lg flex-shrink-0" />

        <div className="flex-1 min-w-0 space-y-3">
          {/* Label skeleton */}
          <div className="h-3 w-24 bg-gray-200 rounded" />

          {/* Wine name skeleton */}
          <div className="h-5 w-3/4 bg-gray-200 rounded" />

          {/* Location skeleton */}
          <div className="h-3 w-1/2 bg-gray-200 rounded" />
        </div>

        {/* Button skeleton */}
        <div className="w-9 h-9 bg-gray-200 rounded-xl flex-shrink-0" />
      </div>

      {/* Explanation skeleton */}
      <div className="mt-4 pt-4 border-t border-gray-100 space-y-2">
        <div className="h-3 w-full bg-gray-200 rounded" />
        <div className="h-3 w-2/3 bg-gray-200 rounded" />
      </div>
    </div>
  );
}
