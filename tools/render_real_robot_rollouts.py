"""Render the supplied real-robot observations and offline-replayed router maps.

Usage: python tools/render_real_robot_rollouts.py --source EXTRACTED_ARCHIVE
The stage choices come from stages.csv, before inspecting the router maps.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import numpy as np
from PIL import Image


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path,
                        default=root/'figures/supp_real_robot_rollouts')
    parser.add_argument('--provenance', type=Path,
                        default=root/'supp/real_robot_rollout_sources.json')
    parser.add_argument('--preview', type=Path, help='Optional PNG preview path.')
    args = parser.parse_args()
    source = args.source
    stages = list(csv.DictReader((source/'stages.csv').open()))
    inventory = json.loads((source/'inventory.json').read_text())
    validation = json.loads((source/'validation.json').read_text())
    assert validation['all_replayed_actions_exact']
    assert validation['max_abs_action_diff'] == 0
    assert validation['provenance'] == 'offline_reconstruction_not_online_telemetry'

    green = '#00783c'
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 7,
        'text.color': green, 'axes.labelcolor': green,
        'xtick.color': green, 'ytick.color': green,
        'pdf.fonttype': 42, 'svg.fonttype': 'none',
        'savefig.facecolor': 'white',
    })
    width, height = 7.05, 7.24
    fig = plt.figure(figsize=(width, height), facecolor='white')
    left, gap, cell_w = .49, .045, 1.57375
    cell_h = cell_w*9/16
    phases = [('approach', 'Approach'), ('grasp_or_contact', 'Contact'),
              ('manipulation', 'Manipulation'),
              ('completion_or_terminal_state', 'Terminal state')]
    tasks = [('stack_bowl', '(a) Stack Bowls'), ('open_lid', '(b) Open Lid')]
    selected = []

    def at_text(x, y, value, **kwargs):
        return fig.text(x/width, 1-y/height, value, color=green, **kwargs)

    def image_axis(x, top, rgb):
        ax = fig.add_axes([x/width, 1-(top+cell_h)/height,
                           cell_w/width, cell_h/height])
        ax.imshow(rgb, extent=(0, 1280, 720, 0), interpolation='antialiased')
        ax.set(xlim=(0, 1280), ylim=(720, 0))
        ax.set_axis_off()
        return ax

    for task_i, (task, title) in enumerate(tasks):
        task_top = .08 + task_i*3.47
        at_text(left, task_top, title, fontsize=8.4, weight='bold', va='top')
        for col, (_, phase_title) in enumerate(phases):
            x = left+col*(cell_w+gap)
            at_text(x+cell_w/2, task_top+.23, phase_title,
                    fontsize=7.2, ha='center', va='center')
        top = task_top+.34
        row_tops = [top, top+cell_h+.19, top+2*(cell_h+.19)]
        manifest = json.loads((source/f'router/{task}/manifest.json').read_text())
        router_records = {int(r['query_id']): r for r in manifest['queries']}
        for row_i, method in enumerate(['Full-context', 'ARROW']):
            at_text(.23, row_tops[row_i]+cell_h/2, method,
                    fontsize=7.2, rotation=90, ha='center', va='center')
            for col, (phase, _) in enumerate(phases):
                stage = next(r for r in stages if r['task'] == task
                             and r['method'] == method and r['phase'] == phase)
                image_path = source/Path(stage['image']).name
                rgb = np.asarray(Image.open(image_path).convert('RGB'))
                assert rgb.shape == (720, 1280, 3)
                x = left+col*(cell_w+gap)
                q = int(stage['query_id']) if stage['query_id'] else None
                record = {
                    'task': task, 'method': method, 'phase': phase,
                    'query_id': q, 'video_time_s': float(stage['video_time_s']),
                    'estimated_video_time': 'estimated' in stage['note'],
                    'rgb_file': image_path.name, 'rgb_sha256': sha256(image_path),
                }
                if method == 'ARROW':
                    npz_path = source/f'router/{task}/query_{q:06d}.npz'
                    assert sha256(npz_path) == router_records[q]['output_sha256']
                    with np.load(npz_path, allow_pickle=False) as data:
                        assert np.array_equal(rgb, data['reference_rgb'])
                        assert int(data['query_id']) == q
                        assert np.array_equal(data['actions'], data['recorded_actions'])
                        assert str(data['provenance']) == validation['provenance']
                        scores = data['block_scores'].copy()
                        mask = data['full_block_mask'].copy()
                        spatial = data['spatial_scores']
                        np.testing.assert_allclose(scores, spatial.reshape(15, 2, 20, 2)
                                                   .mean(axis=(1, 3)), atol=1e-7)
                        assert scores.shape == mask.shape == (15, 20)
                        assert mask.sum() == 100
                        assert scores[mask].min() >= scores[~mask].max()
                        assert int(data['aux_adaptive_future_tokens_out'][0]) == 5040
                    ax = image_axis(x, row_tops[2], rgb)
                    ax.imshow(scores, extent=(0, 1280, 720, 0), interpolation='nearest',
                              cmap='magma', vmin=0, vmax=1, alpha=.55)
                    outlines = []
                    for r, c in np.argwhere(mask):
                        x0, y0 = c*64, r*48
                        outlines.append([(x0, y0), (x0+64, y0), (x0+64, y0+48),
                                         (x0, y0+48), (x0, y0)])
                    ax.add_collection(LineCollection(outlines, colors='white', linewidths=.25))
                    record.update(router_file=str(npz_path.relative_to(source)),
                                  router_sha256=sha256(npz_path), fine_groups=int(mask.sum()),
                                  replay_action_max_abs_diff=0.0,
                                  map_provenance=validation['provenance'])
                image_axis(x, row_tops[row_i], rgb)
                time = float(stage['video_time_s'])
                prefix = r'$\approx$' if record['estimated_video_time'] else ''
                label = (f'q={q}, ' if q is not None else '') + f't={prefix}{time:.1f} s'
                at_text(x+cell_w/2, row_tops[row_i]+cell_h+.065, label,
                        ha='center', va='center', fontsize=6.6)
                selected.append(record)
        at_text(.23, row_tops[2]+cell_h/2, 'ARROW router',
                fontsize=7.2, rotation=90, ha='center', va='center')

    # A shared [0, 1] scale avoids changing the interpretation between queries.
    cax = fig.add_axes([.70/width, .14/height, 1.55/width, .08/height])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0, 1), cmap='magma'),
                      cax=cax, orientation='horizontal', ticks=[0, .5, 1])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=6.5, length=1.5, pad=1)
    at_text(2.45, height-.18, r'Group score $S_g$; white outlines: 100 full-resolution groups',
            fontsize=6.7, va='center')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output.with_suffix('.pdf'), dpi=300,
                metadata={'Title': 'Real-robot rollouts and replayed router scores',
                          'Author': '', 'CreationDate': None, 'ModDate': None})
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.preview, dpi=200)
    plt.close(fig)
    provenance = {
        'source_archive': 'router_and_alignment_2tasks.zip',
        'selection': inventory['selection'], 'map_provenance': inventory['router_provenance'],
        'comparison': 'Separate recorded runs; columns aligned by task phase, not paired reset or wall-clock time.',
        'outcomes': 'Terminal states are displayed without assigning formal success/failure labels.',
        'map_display': 'Provided 15x20 block_scores; fixed magma scale [0,1], alpha 0.55; white outlines from full_block_mask.',
        'image_geometry': 'Full uncropped 1280x720 observations; no synthesized frames.',
        'tokens': {'Full-context': 19200, 'ARROW': 7440, 'ARROW_future': 5040},
        'all_displayed_replays_match_recorded_actions_exactly': True,
        'selected_frames': selected,
    }
    args.provenance.write_text(json.dumps(provenance, indent=2)+'\n')
    print(f'Rendered {len(selected)} real observations and 8 aligned replayed router maps.')


if __name__ == '__main__':
    main()
