<script lang="ts">
	import SpotlightCard from '$lib/components/svelte-bits/SpotlightCard.svelte';
	import { isDarkMode } from '$lib/components/svelte-bits/theme';
	export let title = '';
	export let first = false;
	export let className = '';
</script>

<SpotlightCard
	class="llmw-card w-full {first ? '' : 'mt-4'} {className}"
	theme={$isDarkMode ? 'dark' : 'light'}
	spotlightColor="rgba(139, 92, 246, 0.22)"
	intensity={0.18}
	spotlightSize={320}
	borderGlow={0.8}
>
	{#if title}
		<h3 class="llmw-section-title mb-2 text-xs text-base-600 dark:text-base-400">
			{title}
		</h3>
	{/if}

	<div class="llmw-card-body flex flex-col gap-2.5">
		<slot />
	</div>
</SpotlightCard>
