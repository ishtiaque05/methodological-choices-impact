import argparse

from AgeNorm import AgeNorm
from AggregateAnalysis import AggregateAnalysis
from ChangeKindAnalysis import ChangeKindAnalysis
from SLOCSelection import SLOCSelection
from SizeControl import SizeControl

AGE_THRESHOLD = {
    "no_threshold": 0,
    "6_months": 183,
    "1_yr": 365,
    "2_yrs": 730,
    "3_yrs": 1095,
    "4_yrs": 1460
}


def main():

    args = cli_args()
    print(args)
    if args.prepdata:
        print("starting to prepare data...")
        preparing_data()
    else:
        render_graphs(args)


def cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepdata", type=bool, default=False)
    parser.add_argument("--rq1", type=bool)
    parser.add_argument("--rq2", type=bool)
    parser.add_argument("--rq3", type=bool)
    parser.add_argument("--rq4", type=bool)
    parser.add_argument("--rq5", type=bool)

    return parser.parse_args()


def render_graphs(args):
    if args.rq1:
        render_graph_for_sloc_measurements()
    elif args.rq2:
        render_graph_for_sloc_control()
    elif args.rq3:
        render_graph_for_age_analysis()
    elif args.rq4:
        render_graph_for_change_kind()
    elif args.rq5:
        render_graph_for_aggregate_project_analysis()
    else:
        print("Please pass rq1, rq2, rq3, rq4 or rq5 to render a particular research question graph")


def preparing_data():
    prepare_data_for_age_analysis()
    prepare_data_for_sloc_measures()
    prepare_data_for_size_control()


def prepare_data_for_size_control():
    sizeCtrl = SizeControl()
    sizeCtrl.process("730", apply_change_filter=False, should_filter_get_set=False)
    sizeCtrl.process("730", apply_change_filter=False, should_filter_get_set=True)
    sizeCtrl.get_set_vs_no_get_set_diff(age_threshold=730)


def prepare_data_for_sloc_measures():
    print("Prepare data to examine different SLOC measure with #Revisions and #Bugs...")
    s = SLOCSelection(apply_change_filter=False)

    # Applying 2 years age normalization
    s.process(730, 730, apply_change_filter=False, exclude_method=True)
    s.calculate_corr(730, apply_change_filter=False)

    # For methods that were at least modified once
    s.apply_change_filter = True
    s.process(730, 730, apply_change_filter=True, exclude_method=True)
    s.calculate_corr(730, apply_change_filter=True)

    print("Done preparing dataset to examine different SLOC measure with #Revisions and #Bugs...")


def prepare_data_for_age_analysis():
    print("Process data for age analysis...")
    a = AgeNorm()
    a.process()

    a.age_with_versioning(AGE_THRESHOLD["no_threshold"], apply_change_filter=False)
    a.age_with_versioning(AGE_THRESHOLD["6_months"], apply_change_filter=False)
    a.age_with_versioning(AGE_THRESHOLD["1_yr"], apply_change_filter=False)
    a.age_with_versioning(AGE_THRESHOLD["2_yrs"], apply_change_filter=False)
    a.age_with_versioning(AGE_THRESHOLD["3_yrs"], apply_change_filter=False)
    a.age_with_versioning(AGE_THRESHOLD["4_yrs"], apply_change_filter=False)

    # For methods that were modified once

    a.age_with_versioning(AGE_THRESHOLD["no_threshold"], apply_change_filter=True)
    a.age_with_versioning(AGE_THRESHOLD["6_months"], apply_change_filter=True)
    a.age_with_versioning(AGE_THRESHOLD["1_yr"], apply_change_filter=True)
    a.age_with_versioning(AGE_THRESHOLD["2_yrs"], apply_change_filter=True)
    a.age_with_versioning(AGE_THRESHOLD["3_yrs"], apply_change_filter=True)
    a.age_with_versioning(AGE_THRESHOLD["4_yrs"], apply_change_filter=True)

    # Calculate kendall Tau correlation of SLOC with revisions and bugs for different age range
    a.calculate_corr(AGES=[0, 183, 365, 730, 1095, 1460], should_exclued_less_than_x_years=True,
                     apply_change_filter=True)
    a.calculate_corr(AGES=[0, 183, 365, 730, 1095, 1460], should_exclued_less_than_x_years=True,
                     apply_change_filter=False)

    # Prepare data for interval analysis
    a.interval_age_versioning(age_interval=[0, 183], exclude_x_methods=True)
    a.interval_age_versioning(age_interval=[183, 365], exclude_x_methods=True)
    a.interval_age_versioning(age_interval=[365, 730], exclude_x_methods=True)
    a.interval_age_versioning(age_interval=[730, 1095], exclude_x_methods=True)
    a.interval_age_versioning(age_interval=[1095, 1460], exclude_x_methods=True)
    a.interval_age_versioning(age_interval=[1460, 5], exclude_x_methods=True)

    # Calculate kendall tau correlation of SLOC with revisions and bugs for different interval
    a.calc_interval_corr()

    print("Done preparing data for age analysis....")


def render_graph_for_age_analysis():
    a = AgeNorm()
    a.plot_corr_cdf("kendall", filter_less_than_x_age=True)
    a.process_interval_data_and_plot()


def render_graph_for_sloc_measurements():
    s = SLOCSelection(apply_change_filter=False)
    s.plot_cdf(730, apply_change_filter=False)

    s.apply_change_filter = True
    s.plot_cdf(730, apply_change_filter=True)


def render_graph_for_sloc_control():
    sizeCtrl = SizeControl()
    sizeCtrl.plot_cdf(730, apply_change_filter=False)

    sizeCtrl.render_boxplot("730", "bug_density", "bug_density", apply_change_filter=False, filter_getter_setter=False)
    sizeCtrl.render_boxplot("730", "revision_density", "revision_density", apply_change_filter=False,
                            filter_getter_setter=False)

    sizeCtrl.render_boxplot("730", "bug_density", "bug_density", apply_change_filter=False, filter_getter_setter=True)
    sizeCtrl.render_boxplot("730", "revision_density", "revision_density", apply_change_filter=False,
                            filter_getter_setter=True)

    sizeCtrl.size_ctrl_cliff_delta_analysis("bug_density")
    sizeCtrl.size_ctrl_cliff_delta_analysis("revision_density")


def render_graph_for_aggregate_project_analysis():
    a = AggregateAnalysis()
    a.process(730)


def render_graph_for_change_kind():
    chngKind = ChangeKindAnalysis()
    chngKind.compare_different_changes_age730(730, "change_kind_corr_cdf.pdf")
    chngKind.compare_different_size_changes_age730(730, "revision_diffsize_addition_editdist.pdf")


if __name__ == "__main__":
    main()
