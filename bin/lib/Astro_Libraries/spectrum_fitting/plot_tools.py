import corner
from matplotlib import rcParams
from matplotlib.mlab import detrend_mean
from numpy import array, reshape, empty, ceil, percentile, median, nan
from lib.Plotting_Libraries.dazer_plotter import Plot_Conf
from lib.Plotting_Libraries.sigfig import round_sig
from lib.CodeTools.File_Managing_Tools import Pdf_printer

def label_formatting(line_label):

    label = line_label.replace('_', '\,\,')
    if label[-1] == 'A':
        label = label[0:-1] + '\AA'
    label = '$' + label + '$'

    return label

class Basic_plots(Plot_Conf):

    def __init__(self):

        # Class with plotting tools
        Plot_Conf.__init__(self)

    def prefit_output(self, obj_ssp_fit_flux):

        size_dict = {'figure.figsize': (20, 14), 'axes.labelsize': 16, 'legend.fontsize': 18}
        self.FigConf(plotSize=size_dict)

        self.data_plot(self.input_wave, self.input_continuum, 'Object Input continuum')
        self.data_plot(self.obj_data['obs_wave'], self.obj_data['synth_neb_flux'], 'synth_neb_flux', linestyle = '--')
        self.data_plot(self.input_wave, obj_ssp_fit_flux , 'Stellar Prefit continuum output', linestyle=':')

        #In case of a synthetic observation:
        if 'neb_SED' in self.obj_data:
            self.data_plot(self.input_wave, self.obj_data['neb_SED']['neb_int_norm'], 'Nebular continuum')
            title_label = 'Observed spectrum'
        if 'stellar_flux' in self.obj_data:
            self.data_plot(self.obj_data['obs_wave'], self.obj_data['stellar_flux']/self.obj_data['normFlux_coeff'], 'Stellar continuum')
            self.data_plot(self.obj_data['obs_wave'], self.obj_data['stellar_flux_err']/ self.obj_data['normFlux_coeff'], 'Stellar continuum with uncertainty', linestyle=':')
            title_label = 'Synthetic spectrum'

        self.FigWording(xlabel='Wavelength $(\AA)$', ylabel = 'Observed flux', title = title_label)

        return

    def prefit_comparison(self, obj_ssp_fit_flux):

        size_dict = {'figure.figsize': (20, 14), 'axes.labelsize': 16, 'legend.fontsize': 18}
        self.FigConf(plotSize=size_dict)

        self.data_plot(self.input_wave, self.obj_data['flux_norm'], 'Object normed flux')
        self.data_plot(self.input_wave, self.obj_data['synth_neb_flux'], 'Nebular continuum')
        self.data_plot(self.input_wave, obj_ssp_fit_flux + self.obj_data['synth_neb_flux'], 'Prefit continuum output', linestyle=':')

        self.FigWording(xlabel='Wavelength $(\AA)$', ylabel='Observed flux', title='SSPs continuum prefit')

        return

    def prefit_ssps(self):

        size_dict = {'figure.figsize': (20, 14), 'axes.labelsize': 16, 'legend.fontsize': 18}
        self.FigConf(plotSize=size_dict)

        #TODO This function should go to my collection
        ordinal_generator = lambda n: "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
        ordinal_bases = [ordinal_generator(n) for n in range(len(self.sspPrefit_Coeffs))]

        counter = 0
        for i in range(len(self.onBasesFluxNorm)):
            if self.sspPrefit_Coeffs[i] > self.lowlimit_sspContribution:
                counter += 1
                label_i = '{} base: flux coeff {}, norm coeff {:.2E}'.format(ordinal_bases[i], self.sspPrefit_Coeffs[i], self.onBasesFluxNormCoeffs[i])
                self.data_plot(self.onBasesWave, self.onBasesFluxNorm[i], label_i)

        self.area_fill(self.ssp_lib['norm_interval'][0], self.ssp_lib['norm_interval'][1], 'Norm interval: {} - {}'.format(self.ssp_lib['norm_interval'][0], self.ssp_lib['norm_interval'][1]), alpha=0.5)

        title = 'SSP prefit contributing stellar populations {}/{}'.format((self.sspPrefit_Coeffs > self.lowlimit_sspContribution).sum(), len(self.onBasesFluxNorm))
        self.FigWording(xlabel='Wavelength $(\AA)$', ylabel = 'Normalized flux', title = title)

        return

    def masked_observation(self):

        size_dict = {'figure.figsize': (20, 14), 'axes.labelsize': 16, 'legend.fontsize': 18}
        self.FigConf(plotSize=size_dict)

        self.data_plot(self.obj_data['obs_wave'], self.obj_data['flux_norm'], 'Normalized observation')
        self.data_plot(self.input_wave, self.input_continuum, 'Masked observation', linestyle='--')

        self.FigWording(xlabel='Wavelength $(\AA)$', ylabel = 'Observed flux', title = 'Spectrum masks')

        return

    def resampled_observation(self):

        size_dict = {'figure.figsize': (20, 14), 'axes.labelsize': 16, 'legend.fontsize': 18}
        self.FigConf(plotSize=size_dict)

        self.data_plot(self.obj_data['obs_wave'], self.obj_data['obs_flux'], 'Observed spectrum')
        self.data_plot(self.obj_data['wave_resam'], self.obj_data['flux_resam'], 'Resampled spectrum', linestyle='--')
        self.data_plot(self.obj_data['wave_resam'], self.obj_data['flux_norm'] * self.obj_data['normFlux_coeff'], r'Normalized spectrum $\cdot$ {:.2E}'.format(self.obj_data['normFlux_coeff']), linestyle=':')
        self.area_fill(self.obj_data['norm_interval'][0], self.obj_data['norm_interval'][1], 'Norm interval: {} - {}'.format(self.obj_data['norm_interval'][0], self.obj_data['norm_interval'][1]), alpha=0.5)

        self.FigWording(xlabel='Wavelength $(\AA)$', ylabel = 'Observed flux', title = 'Resampled observation')

        return

    def traces_plot(self, traces, database, stats_dic):

        # Number of traces to plot
        n_traces = len(traces)

        # Declare figure format
        size_dict = {'figure.figsize': (14, 20), 'axes.titlesize':26, 'axes.labelsize': 24, 'legend.fontsize': 18}
        self.FigConf(plotSize=size_dict, Figtype='Grid', n_columns=1, n_rows=n_traces)

        # Generate the color map
        self.gen_colorList(0, n_traces)

        # Plot individual traces
        for i in range(n_traces):

            # Current trace
            trace_code = traces[i]
            trace_array = stats_dic[trace_code]['trace']

            # Label for the plot
            mean_value = stats_dic[trace_code]['mean']
            std_dev = stats_dic[trace_code]['standard deviation']
            if mean_value > 0.001:
                label = r'{} = ${}$ $\pm${}'.format(self.labels_latex_dic[trace_code], round_sig(mean_value, 4),
                                                    round_sig(std_dev, 4))
            else:
                label = r'{} = ${:.3e}$ $\pm$ {:.3e}'.format(self.labels_latex_dic[trace_code], mean_value, std_dev)

            # Plot the data
            self.Axis[i].plot(trace_array, label=label, color=self.get_color(i))
            self.Axis[i].axhline(y=mean_value, color=self.get_color(i), linestyle='--')
            self.Axis[i].set_ylabel(self.labels_latex_dic[trace_code])

            if i < n_traces - 1:
                self.Axis[i].set_xticklabels([])

            # Add legend
            self.legend_conf(self.Axis[i], loc=2)

        return

    def posteriors_plot(self, traces, database, stats_dic):

        # Number of traces to plot
        n_traces = len(traces)

        # Declare figure format
        size_dict = {'figure.figsize': (14, 20), 'axes.titlesize':22, 'axes.labelsize': 22, 'legend.fontsize': 14}
        self.FigConf(plotSize=size_dict, Figtype='Grid', n_columns=1, n_rows=n_traces)

        # Generate the color map
        self.gen_colorList(0, n_traces)

        # Plot individual traces
        for i in range(len(traces)):

            # Current trace
            trace_code = traces[i]
            mean_value = stats_dic[trace_code]['mean']
            trace_array = stats_dic[trace_code]['trace']

            # Plot HDP limits
            HDP_coords = stats_dic[trace_code]['95% HPD interval']
            for HDP in HDP_coords:

                if mean_value > 0.001:
                    label_limits = 'HPD interval: {} - {}'.format(round_sig(HDP_coords[0], 4),
                                                                  round_sig(HDP_coords[1], 4))
                    label_mean = 'Mean value: {}'.format(round_sig(mean_value, 4))
                else:
                    label_limits = 'HPD interval: {:.3e} - {:.3e}'.format(HDP_coords[0], HDP_coords[1])
                    label_mean = 'Mean value: {:.3e}'.format(mean_value)

                self.Axis[i].axvline(x=HDP, label=label_limits, color='grey', linestyle='dashed')

            self.Axis[i].axvline(x=mean_value, label=label_mean, color='grey', linestyle='solid')
            self.Axis[i].hist(trace_array, histtype='stepfilled', bins=35, alpha=.7, color=self.get_color(i), normed=False)

            #Add true value if available
            if 'true_value' in stats_dic[trace_code]:
                value_true = stats_dic[trace_code]['true_value']
                label_true = 'True value {:.3e}'.format(value_true)
                self.Axis[i].axvline(x=value_true, label=label_true, color='black', linestyle='solid')

            # Figure wording
            self.Axis[i].set_ylabel(self.labels_latex_dic[trace_code])
            self.legend_conf(self.Axis[i], loc=2)

    def fluxes_distribution(self, lines_list, function_key, db, db_dict, true_values = None):

        # Number of traces to plot
        n_lines = len(lines_list)

        # Declare figure format
        size_dict = {'figure.figsize': (14, 20), 'axes.titlesize':20, 'axes.labelsize': 20, 'legend.fontsize': 14}
        self.FigConf(plotSize=size_dict, Figtype='Grid', n_columns=1, n_rows=n_lines)

        # Generate the color map
        self.gen_colorList(0, n_lines)

        # Flux statistics
        traces_array    = db_dict[function_key]['trace']
        median_values   = median(db_dict[function_key]['trace'], axis=0)
        p16th_fluxes    = percentile(db_dict[function_key]['trace'], 16, axis=0)
        p84th_fluxes    = percentile(db_dict[function_key]['trace'], 84, axis=0)

        # Plot individual traces
        for i in range(n_lines):

            #Current line
            label       = label_formatting(lines_list[i])
            trace       = traces_array[:,i]
            median_flux = median_values[i]

            # Plot HDP limits
            for HDP in [p16th_fluxes[i], p84th_fluxes[i]]:

                if median_flux > 0.001:
                    label_limits = 'HPD interval: {} - {}'.format(round_sig(p16th_fluxes[i], 4), round_sig(p84th_fluxes[i], 4))
                    label_mean = 'Mean value: {}'.format(round_sig(median_flux, 4))
                else:
                    label_limits = 'HPD interval: {:.3e} - {:.3e}'.format(p16th_fluxes[i], p84th_fluxes[i])
                    label_mean = 'Mean value: {:.3e}'.format(median_flux)

                self.Axis[i].axvline(x=HDP, label=label_limits, color='grey', linestyle='dashed')

            self.Axis[i].axvline(x=median_flux, label=label_mean, color='grey', linestyle='solid')
            self.Axis[i].hist(trace, histtype='stepfilled', bins=35, alpha=.7, color=self.get_color(i), normed=False)

            if  true_values is not None:
                true_value = true_values[i]
                label_true = 'True value: {}'.format(round_sig(true_value, 3))
                self.Axis[i].axvline(x=true_value, label=label_true, color='black', linestyle='solid')

            # Plot wording
            self.Axis[i].set_ylabel(label)
            self.legend_conf(self.Axis[i], loc=2)

        return

    def acorr_plot(self, traces, database, stats_dic, n_columns=4, n_rows=2):

        # Number of traces to plot
        n_traces = len(traces)

        # Declare figure format
        size_dict = {'figure.figsize': (14, 14), 'axes.titlesize': 20, 'legend.fontsize': 10}
        self.FigConf(plotSize=size_dict, Figtype='Grid', n_columns=n_columns, n_rows=n_rows)

        # Generate the color map
        self.gen_colorList(0, n_traces)

        # Plot individual traces
        for i in range(n_traces):

            # Current trace
            trace_code = traces[i]

            label = self.labels_latex_dic[trace_code]

            trace_array = stats_dic[trace_code]['trace']

            if trace_code != 'ChiSq':
                maxlags = min(len(trace_array) - 1, 100)
                self.Axis[i].acorr(x=trace_array, color=self.get_color(i), detrend=detrend_mean, maxlags=maxlags)

            else:
                # Apano momentaneo
                chisq_adapted = reshape(trace_array, len(trace_array))
                maxlags = min(len(chisq_adapted) - 1, 100)
                self.Axis[i].acorr(x=chisq_adapted, color=self.get_color(i), detrend=detrend_mean, maxlags=maxlags)

            self.Axis[i].set_xlim(0, maxlags)
            self.Axis[i].set_title(label)

        return

    def corner_plot(self, traces, database, stats_dic, plot_true_values=False):

        # Set figure conf
        sizing_dict = {}
        sizing_dict['figure.figsize'] = (14, 14)
        sizing_dict['legend.fontsize'] = 30
        sizing_dict['axes.labelsize'] = 30
        sizing_dict['axes.titlesize'] = 15
        sizing_dict['xtick.labelsize'] = 12
        sizing_dict['ytick.labelsize'] = 12

        rcParams.update(sizing_dict)

        # Reshape plot data
        list_arrays = []
        labels_list = []
        for trace_code in traces:
            trace_array = stats_dic[trace_code]['trace']
            list_arrays.append(trace_array)
            labels_list.append(self.labels_latex_dic[trace_code])
        traces_array = array(list_arrays).T


        true_values = empty(len(traces))
        for i in range(len(traces)):
            if 'true_value' in stats_dic[traces[i]]:
                true_values[i] = stats_dic[traces[i]]['true_value']
            else:
                true_values[i] = None

        #Generate the plot
        self.Fig = corner.corner(traces_array[:, :], fontsize=30, labels=labels_list, quantiles=[0.16, 0.5, 0.84],
                                 show_titles=True, title_args={"fontsize": 200}, truths=true_values,
                                 title_fmt='0.3f')



        # # Make
        # if plot_true_values:
        #
        #     true_values = empty(len(traces))
        #     for i in range(len(traces)):
        #         if 'true_value' in stats_dic[traces[i]]:
        #             true_values[i] = stats_dic[traces[i]]['true_value']
        #         else:
        #             true_values[i] = None
        #
        #     self.Fig = corner.corner(traces_array[:, :], fontsize=30, labels=labels_list, quantiles=[0.16, 0.5, 0.84],
        #                              show_titles=True, title_args={"fontsize": 200}, truths=true_values,
        #                              title_fmt='0.3f')
        # else:
        #     self.Fig = corner.corner(traces_array[:, :], fontsize=30, labels=labels_list, quantiles=[0.16, 0.5, 0.84],
        #                              show_titles=True, title_args={"fontsize": 200}, title_fmt='0.3f')

        return

class Basic_tables(Pdf_printer):

    def __init__(self):

        # Class with pdf tools
        Pdf_printer.__init__(self)

    def table_mean_outputs(self, table_address, parameters_list, db, db_dict, true_values = None):

        # Table headers
        headers = ['Parameter', 'True value', 'Mean', 'Standard deviation', 'Number of points', 'Median', r'$16^{th}$ $percentil$', r'$84^{th}$ $percentil$']

        # Generate pdf
        self.create_pdfDoc(table_address, pdf_type='table')
        self.pdf_insert_table(headers)

        #Loop around the parameters
        for param in parameters_list:

            # Label for the plot
            label       = self.labels_latex_dic[param]
            mean_value  = db_dict[param]['mean']
            std         = db_dict[param]['standard deviation']
            n_traces    = db_dict[param]['n']
            median      = db_dict[param]['median']
            p_16th      = db_dict[param]['16th_p']
            p_84th      = db_dict[param]['84th_p']

            if 'true_value' in db_dict[param]:
                true_value = db_dict[param]['true_value']
            else:
                true_value = 'None'

            self.addTableRow([label, true_value, mean_value, std, n_traces, median, p_16th, p_84th], last_row=False if parameters_list[-1] != param else True)

        self.generate_pdf(clean_tex=True)

        return

    def table_line_fluxes(self, table_address, lines_list, function_key, db, db_dict, true_values = None):

        # Generate pdf
        self.create_pdfDoc(table_address, pdf_type='table')

        # Table headers
        headers = ['Line Label', 'Mean', 'Standard deviation', 'Median', r'$16^{th}$ $percentil$', r'$84^{th}$ $percentil$']

        if true_values is not None:
            headers.insert(1, 'True value')

        self.pdf_insert_table(headers)

        mean_line_values    = db_dict[function_key]['trace'].mean(axis=0)
        std_line_values     = db_dict[function_key]['trace'].std(axis=0)
        median_line_values  = median(db_dict[function_key]['trace'], axis=0)
        p16th_line_values   = percentile(db_dict[function_key]['trace'],16, axis=0)
        p84th_line_values   = percentile(db_dict[function_key]['trace'],84, axis=0)

        for i in range(len(lines_list)):

            #Operations to format the label name "H1_4861A"
            label = label_formatting(lines_list[i])

            row_i = [label, mean_line_values[i], std_line_values[i], median_line_values[i], p16th_line_values[i], p84th_line_values[i]]

            if true_values is not None:
                row_i.insert(1, true_values[i])

            self.addTableRow(row_i, last_row=False if lines_list[-1] != lines_list[i] else True)

        self.generate_pdf(clean_tex=True)

class MCMC_printer(Basic_plots, Basic_tables):

    def __init__(self):

        # Supporting classes
        Basic_plots.__init__(self)
        Basic_tables.__init__(self)

    def plot_prefit_data(self):

        # TODO this calculation should not be here... we should be able to change it to prepare_data or somewhere else
        ssp_grid_i_norm = self.physical_SED_model(self.ssp_lib['wave_resam'], self.obj_data['wave_resam'],
                self.onBasesFluxNorm, self.ssp_lib['Av_sspPrefit'], 0.0, self.ssp_lib['sigma_sspPrefit'], self.Rv_model)

        obj_ssp_fit_flux = ssp_grid_i_norm.dot(self.sspPrefit_Coeffs)

        # Continua components from ssp prefit
        self.prefit_comparison(obj_ssp_fit_flux)
        self.savefig(self.input_folder + 'prefit_prefitOutput', resolution=200)

        # Prefit SSPs norm plot
        self.prefit_ssps()
        self.savefig(self.input_folder + 'prefit_NormSsps', resolution=200)

        # Plot input data
        self.prefit_output(obj_ssp_fit_flux)
        self.savefig(self.input_folder + 'prefit_components', resolution=200)

        # Spectrum masking
        self.masked_observation()
        self.savefig(self.input_folder + 'spectrum_mask', resolution=200)

        # Spectrum resampling
        self.resampled_observation()
        self.savefig(self.input_folder + 'resampled_spectra', resolution=200)

        # Stellar prefit Traces
        self.traces_plot(['Av_star', 'sigma_star'], self.ssp_lib['db_sspPrefit'], self.ssp_lib['dbDict_sspPrefit'])
        self.save_manager(self.input_folder + 'PrefitTracesPlot', save=True, save_pickle=False)

        # Stellar prefit Posteriors
        self.posteriors_plot(['Av_star', 'sigma_star'], self.ssp_lib['db_sspPrefit'], self.ssp_lib['dbDict_sspPrefit'])
        self.save_manager(self.input_folder + 'PrefitPosteriorPlot', save=True, save_pickle=False)

        return

    def plot_ouput_data(self, database_address, db, db_dict, params_list):

        print '-Printing output data:'

        # Table mean values
        print '--Model parameters table'
        self.table_mean_outputs(database_address + '_meanOutput', params_list, db, db_dict)

        # Recombination fluxes
        if 'recomb_lines' in self.fitting_components:
            print '--Recombination lines table'
            self.table_line_fluxes(database_address + '_FluxesRecomb', self.obj_data['recombLine_labes'], 'calc_recomb_fluxes', db, db_dict, true_values=self.recomb_fluxes)
            self.fluxes_distribution(self.obj_data['recombLine_labes'], 'calc_recomb_fluxes', db, db_dict, true_values=self.recomb_fluxes)
            self.savefig(database_address + '_FluxesRecomb_posteriors', resolution=200)

        # Collisional excited fluxes
        if 'colExcited_lines' in self.fitting_components:
            print '--Colisional lines table:'
            self.table_line_fluxes(database_address + '_FluxesColExc', self.obj_data['colLine_labes'], 'calc_colExcit_fluxes', db, db_dict, true_values=self.colExc_fluxes)
            self.fluxes_distribution(self.obj_data['colLine_labes'], 'calc_colExcit_fluxes', db, db_dict, true_values=self.colExc_fluxes)
            self.savefig(database_address + '_FluxesColExc_posteriors', resolution=200)

        # Traces
        print '--Traces diagram'
        self.traces_plot(params_list, db, db_dict)
        self.savefig(database_address + '_TracesPlot', resolution=200)

        # Posteriors
        print '--Model parameters posterior diagram'
        self.posteriors_plot(params_list, db, db_dict)
        self.savefig(database_address + '_PosteriorPlot', resolution=200)

        # Corner plot
        print '--Scatter plot matrix'
        self.corner_plot(params_list, db, db_dict)
        self.savefig(database_address + '_CornerPlot', resolution=200)

        # Acorrelation
        print '--Acorrelation plot'
        self.acorr_plot(params_list, db, db_dict, n_columns=4, n_rows=int(ceil(len(params_list)/4.0)))
        self.savefig(database_address + '_Acorrelation', resolution=200)

        return
