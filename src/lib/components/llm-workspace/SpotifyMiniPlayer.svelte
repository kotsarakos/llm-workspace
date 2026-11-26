<!--
	Spotify "now playing" card for the sidebar.
	Polls the Spotify MCP server's read-only /now-playing endpoint and hides itself
	when the server is not running, the API is not connected or nothing is playing.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import TiltedCard from '$lib/components/svelte-bits/TiltedCard.svelte';
	import GlareHover from '$lib/components/svelte-bits/GlareHover.svelte';
	import { isDarkMode } from '$lib/components/svelte-bits/theme';
	import { SPOTIFY_NOW_PLAYING_URL } from './config';

	type Track = {
		title: string;
		artists: string;
		album: string;
		image: string;
		is_playing: boolean;
		device: string;
	};

	let { className = '' }: { className?: string } = $props();
	let track = $state<Track | null>(null);

	onMount(() => {
		let timer: ReturnType<typeof setTimeout>;
		let stopped = false;

		const schedule = () => {
			if (!stopped) timer = setTimeout(poll, track ? 5000 : 15000);
		};

		async function poll() {
			if (document.hidden) return schedule();
			try {
				const res = await fetch(SPOTIFY_NOW_PLAYING_URL, { cache: 'no-store' });
				const data = await res.json();
				track = data?.available && data.track?.title ? data.track : null;
			} catch {
				track = null; // server not running: stay hidden
			}
			schedule();
		}

		poll();
		return () => {
			stopped = true;
			clearTimeout(timer);
		};
	});
</script>

{#if track}
	<div class="px-2 pb-1 {className}">
		<GlareHover
			width="100%"
			background={$isDarkMode ? 'rgba(139, 92, 246, 0.10)' : 'rgba(139, 92, 246, 0.08)'}
			borderColor="rgba(139, 92, 246, 0.25)"
			borderRadius="14px"
			glareColor="#c4b5fd"
			glareOpacity={0.35}
		>
			<div class="flex w-full items-center gap-3 p-2" title="{track.title} — {track.artists}">
				{#if track.image}
					<TiltedCard
						imageSrc={track.image}
						altText="{track.album} cover"
						containerHeight="44px"
						containerWidth="44px"
						imageHeight="44px"
						imageWidth="44px"
						rotateAmplitude={16}
						scaleOnHover={1.12}
						showTooltip={false}
						flipOnClick={false}
						gyroscope={false}
						intro={false}
						radius={9}
						glare={0.6}
					/>
				{/if}
				<div class="min-w-0 flex-1 leading-tight">
					<div class="truncate text-[0.8125rem] font-medium text-base-900 dark:text-base-50">
						{track.title}
					</div>
					<div class="truncate text-xs text-base-500 dark:text-base-400">{track.artists}</div>
					<div class="mt-0.5 flex items-center gap-1 text-[0.6875rem] text-violet-500 dark:text-violet-300">
						<span class="eq" class:paused={!track.is_playing} aria-hidden="true">
							<span></span><span></span><span></span>
						</span>
						<span class="truncate">{track.is_playing ? 'Playing' : 'Paused'} · {track.device}</span>
					</div>
				</div>
			</div>
		</GlareHover>
	</div>
{/if}

<style>
	.eq {
		display: inline-flex;
		align-items: flex-end;
		gap: 1px;
		height: 9px;
	}
	.eq span {
		width: 2px;
		height: 100%;
		border-radius: 1px;
		background: currentColor;
		animation: eq 0.9s ease-in-out infinite;
	}
	.eq span:nth-child(2) {
		animation-delay: -0.3s;
	}
	.eq span:nth-child(3) {
		animation-delay: -0.6s;
	}
	.eq.paused span {
		animation: none;
		height: 30%;
	}
	@keyframes eq {
		0%,
		100% {
			height: 30%;
		}
		50% {
			height: 100%;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.eq span {
			animation: none;
		}
	}
</style>
