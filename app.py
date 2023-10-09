from viktor import ViktorController
from viktor.core import File
from viktor.parametrization import (
    ViktorParametrization, 
    OptionField,  
    Text, 
    NumberField, 
    Section, 
    ActionButton, 
    OptionField,
    LineBreak,
    DownloadButton,
    IntegerField)
from viktor.views import (
    ImageResult, 
    ImageView)
from viktor.result import (
    DownloadResult)

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from io import StringIO
import fkit




class Parametrization(ViktorParametrization):
    section1 = Section("Introduction")
    section1.introduction = Text(
        """
# 🏙 Reinforced-Concrete Section Analysis

This app performs moment-curvature and PM interaction analysis of reinforced-concrete sections.

Easy as 1-2-3:

1. Define material properties
2. Create section
3. Run analysis
        """)
    section1.unit_option = OptionField('Please select a unit system:', options=['Metric (SI)', 'Imperial (US)'], default='Imperial (US)', variant="radio")


    section2 = Section("STEP 1: DEFINE FIBER MATERIAL PROPERTIES")
    section2.text1 = Text("**Unconfined concrete [(Hognestad Model)](https://github.com/wcfrobert/fkit/tree/master/doc#hognestad)**")
    section2.fpc1 = NumberField("$f'_c$", min=0, max=200, default=4, suffix="ksi or MPa", description="Unconfined Concrete compressive strength")

    section2.text2 = Text("**Confined concrete [(Mander Model)](https://github.com/wcfrobert/fkit/tree/master/doc#mander)**")
    section2.fpc2 = NumberField("$f'_c$", min=0, max=200, default=6, suffix="ksi or MPa", description="Confined concrete compressive strength")
    section2.eo = NumberField('$\\epsilon_o$', min=0, max=1, default=0.004, description="Strain at peak stress. Ranges from 0.002 for unconfined concrete to 0.01 for confined concrete")
    section2.emax = NumberField('$\\epsilon_u$', min=0, max=1, default=0.014, description="Ultimate or spalling strain. Ranges from 0.003 to 0.008 for unconfined concrete and can be as high as 0.04 for confined concrete")

    section2.text3 = Text("**Reinforcing bar steel [(Bilinear Model)](https://github.com/wcfrobert/fkit/tree/master/doc#bilinear)**")
    section2.fy = NumberField('$f_y$', min=0, max=10000, default=60, suffix="ksi or MPa", description="Steel yield strength")
    section2.Es = NumberField('$E_s$', min=0, max=1e6, default=29000, suffix="ksi or MPa", description="Steel elastic modulus")



    section3 = Section("STEP 2: DEFINE SECTION")
    section3.text1 = Text("**Rectangular Section with Confined Core**")
    section3.width = NumberField('Width', min=0, max=10000, default=24, suffix="in or mm", description = "Section width (along horizontal axis)")
    section3.height = NumberField('Height', min=0, max=10000, default=36, suffix="in or mm", description = "Section height (along vertical axis)")
    section3.cover = NumberField('Cover', min=0, max=10000, default=2.5, suffix="in or mm", description = "Cover to center of outer rebar")
    section3.rotate = NumberField('Rotate Section', min=0, max=360, default=0, suffix="degrees", description = "Rotate the section counter-clockwise if desired")

    section3.text2 = Text("**Top layer:**")
    section3.top_bar_area = NumberField('Bar area', min=0, max=10000, default=0.79, suffix="in${}^2$ or mm${}^2$", description="Area of a single rebar")
    section3.top_bar_nx= IntegerField('Number of Bars', min=0, max=100, default=3, description="Number of bars across the width evenly spaced")

    section3.text3 = Text("**Mid layer:**")
    section3.mid_bar_area = NumberField('Bar area', min=0, max=10000, default=0.79, suffix="in${}^2$ or mm${}^2$", description="Area of a single rebar")
    section3.mid_bar_nx= IntegerField('Number of Bars', min=0, max=100, default=2, description="Number of bars across the width evenly spaced")

    section3.text4 = Text("**Bottom layer:**")
    section3.bot_bar_area = NumberField('Bar area', min=0, max=10000, default=0.79, suffix="in${}^2$ or mm${}^2$", description="Area of a single rebar")
    section3.bot_bar_nx= IntegerField('Number of Bars', min=0, max=100, default=3, description="Number of bars across the width evenly spaced")

    section3.text5 = Text("""
Many other section geometries are available through [fiber-kit.](https://github.com/wcfrobert/fkit/) and will be implemented in VIKTOR soon!
        """)



    section4 = Section("STEP 3: RUN ANALYSIS AND DOWNLOAD DATA")
    section4.text1 = Text("""
Click update to refresh results. Moment curvature analysis will be performed to the user-specified target curvature and with the geometry/fibers defined above.
PM interaction analysis will be performed in accordance to the assumption of ACI 318-19 (e.g. rectangular stress block, elastic-perfect-plastic steel, spalling strain of 0.003, etc)
        """)
    section4.pu = NumberField('Applied Axial Demand', min=-1e6, max=1e6, default=-180, suffix="kips or N", flex=60, description="Specify an applied tension or compression load. Note negative (-) is compression, positive (+) is tension.")
    section4.phi_target = NumberField('Target Curvature', min=0, max=10000, default=0.0002, suffix="1/in or 1/mm", flex=60, description="Specify how far to push the section. Yield curvature can be approximated as 0.01/d where d is the section depth.")
    section4.linebreak1 = LineBreak()
    section4.text2=Text("")
    section4.linebreak1 = LineBreak()
    section4.button2 = DownloadButton('Download moment curvature data', method='download_mk', flex=60)
    section4.button3 = DownloadButton('Download PM interaction data', method='download_pm', flex=60)
    section4.disclaimer = Text("""
For educational use only. Made with [fiber-kit.](https://github.com/wcfrobert/fkit/)
        """)






class Controller(ViktorController):
    label = 'fiber-kit Reinforce Concrete Section Analysis'
    parametrization = Parametrization

    @ImageView("Section and Fibers", duration_guess=10)
    def plot_section_fiber(self, params, **kwargs):
        # define fibers
        fiber_unconfined = fkit.patchfiber.Todeschini(fpc=params.section2.fpc1)

        fiber_confined   = fkit.patchfiber.Mander(fpc=params.section2.fpc2,
                                                  eo=params.section2.eo, 
                                                  emax=params.section2.emax, 
                                                  default_color="gray")

        fiber_steel      = fkit.nodefiber.Bilinear(fy=params.section2.fy, 
                                                   Es=params.section2.Es)

        # create section
        section = fkit.sectionbuilder.rectangular_confined(width = params.section3.width, 
                                                           height = params.section3.height, 
                                                           cover = params.section3.cover, 
                                                           top_bar = [params.section3.top_bar_area, params.section3.top_bar_nx, 1, 0], 
                                                           bot_bar = [params.section3.bot_bar_area, params.section3.bot_bar_nx, 1, 0], 
                                                           core_fiber = fiber_confined, 
                                                           cover_fiber = fiber_unconfined, 
                                                           steel_fiber = fiber_steel,
                                                           mesh_nx=0.85,
                                                           mesh_ny=0.85)
        if params.section3.mid_bar_area!=0 and params.section3.mid_bar_nx!=0:
            section.add_bar_group(xo=-params.section3.width/2+params.section3.cover, 
                                  yo=0, 
                                  b=params.section3.width - params.section3.cover*2, 
                                  h=0, 
                                  nx=params.section3.mid_bar_nx, 
                                  ny=1, 
                                  area=params.section3.mid_bar_area, 
                                  perimeter_only=True, fiber=fiber_steel)

        section.mesh(rotate = params.section3.rotate)


        # plot geometry
        fig, axs = plt.subplots(1,3,figsize=(16,9))
        for f in section.node_fibers:
            radius = (f.area/3.1415926)**(0.5)
            axs[0].add_patch(patches.Circle(f.coord,radius=radius,facecolor=f.default_color,edgecolor="black",zorder=2,lw=2))
        for f in section.patch_fibers:
            axs[0].add_patch(patches.Polygon(np.array(f.vertices),closed=True,facecolor=f.default_color,edgecolor="black",zorder=1,lw=1.0))
        axs[0].scatter(section.centroid[0], section.centroid[1], c="red", marker="x",linewidth=3, s=240, zorder=3)
        axs[0].xaxis.grid()
        axs[0].yaxis.grid()
        axs[0].set_axisbelow(True)
        axs[0].set_aspect('equal', 'box')

        # plot steel fibers
        x_limit = [-0.005, 0.005]
        strain_x = np.linspace(x_limit[0],x_limit[1],200)
        stress_y = [fiber_steel.stress_strain(a) for a in strain_x]
        axs[1].plot(strain_x,stress_y,c="dodgerblue",lw=2.5,label="Steel-Bilinear")
        axs[1].legend(loc="upper left")
        axs[1].set_xlim(x_limit)
        axs[1].set_xlabel("Strain")
        axs[1].set_ylabel("Stress")
        axs[1].xaxis.grid()
        axs[1].yaxis.grid()
        axs[1].axhline(y=0, color = "black", linestyle="-", lw = 0.8)
        axs[1].axvline(x=0, color = "black", linestyle="-", lw = 0.8)

        # plot concrete fibers
        x_limit = [-0.015, 0.001]
        strain_x = np.linspace(x_limit[0],x_limit[1],200)
        stress_y1 = [fiber_unconfined.stress_strain(a) for a in strain_x]
        stress_y2 = [fiber_confined.stress_strain(a) for a in strain_x]
        axs[2].plot(strain_x,stress_y1,c="red",lw=2.5, label="Concrete-Unconfined")
        axs[2].plot(strain_x,stress_y2,c="seagreen",lw=2.5, label="Concrete-Confined")
        axs[2].legend(loc="upper left")
        axs[2].set_xlim(x_limit)
        axs[2].set_xlabel("Strain")
        axs[2].set_ylabel("Stress")
        axs[2].xaxis.grid()
        axs[2].yaxis.grid()
        axs[2].axhline(y=0, color = "black", linestyle="-", lw = 0.8)
        axs[2].axvline(x=0, color = "black", linestyle="-", lw = 0.8)
        axs[2].invert_xaxis()
        axs[2].invert_yaxis()


        fig.suptitle("Section and Fiber Preview", fontweight="bold")
        plt.tight_layout()

        svg_data = StringIO()
        fig.savefig(svg_data, format='svg')
        plt.close()
        return ImageResult(svg_data)




    @ImageView("Moment Curvature", duration_guess=10)
    def plot_mk(self, params, **kwargs):
        # define fibers
        fiber_unconfined = fkit.patchfiber.Todeschini(fpc=params.section2.fpc1)

        fiber_confined   = fkit.patchfiber.Mander(fpc=params.section2.fpc2,
                                                  eo=params.section2.eo, 
                                                  emax=params.section2.emax, 
                                                  default_color="gray")

        fiber_steel      = fkit.nodefiber.Bilinear(fy=params.section2.fy, 
                                                   Es=params.section2.Es)

        # create section
        section = fkit.sectionbuilder.rectangular_confined(width = params.section3.width, 
                                                           height = params.section3.height, 
                                                           cover = params.section3.cover, 
                                                           top_bar = [params.section3.top_bar_area, params.section3.top_bar_nx, 1, 0], 
                                                           bot_bar = [params.section3.bot_bar_area, params.section3.bot_bar_nx, 1, 0], 
                                                           core_fiber = fiber_confined, 
                                                           cover_fiber = fiber_unconfined, 
                                                           steel_fiber = fiber_steel,
                                                           mesh_nx=0.85,
                                                           mesh_ny=0.85)
        if params.section3.mid_bar_area!=0 and params.section3.mid_bar_nx!=0:
            section.add_bar_group(xo=-params.section3.width/2+params.section3.cover, 
                                  yo=0, 
                                  b=params.section3.width - params.section3.cover*2, 
                                  h=0, 
                                  nx=params.section3.mid_bar_nx, 
                                  ny=1, 
                                  area=params.section3.mid_bar_area, 
                                  perimeter_only=True, fiber=fiber_steel)

        section.mesh(rotate = params.section3.rotate)

        # moment-curvature analysis
        MK_results = section.run_moment_curvature(phi_target=params.section4.phi_target, P=params.section4.pu)

        # plot results
        fig = fkit.plotter.plot_MK(section)


        svg_data = StringIO()
        fig.savefig(svg_data, format='svg')
        plt.close()
        return ImageResult(svg_data)




    @ImageView("PM Interaction", duration_guess=10)
    def plot_pm(self, params, **kwargs):
        # define fibers
        fiber_unconfined = fkit.patchfiber.Todeschini(fpc=params.section2.fpc1)

        fiber_confined   = fkit.patchfiber.Mander(fpc=params.section2.fpc2,
                                                  eo=params.section2.eo, 
                                                  emax=params.section2.emax, 
                                                  default_color="gray")

        fiber_steel      = fkit.nodefiber.Bilinear(fy=params.section2.fy, 
                                                   Es=params.section2.Es)

        # create section
        section = fkit.sectionbuilder.rectangular_confined(width = params.section3.width, 
                                                           height = params.section3.height, 
                                                           cover = params.section3.cover, 
                                                           top_bar = [params.section3.top_bar_area, params.section3.top_bar_nx, 1, 0], 
                                                           bot_bar = [params.section3.bot_bar_area, params.section3.bot_bar_nx, 1, 0], 
                                                           core_fiber = fiber_confined, 
                                                           cover_fiber = fiber_unconfined, 
                                                           steel_fiber = fiber_steel,
                                                           mesh_nx=0.85,
                                                           mesh_ny=0.85)
        if params.section3.mid_bar_area!=0 and params.section3.mid_bar_nx!=0:
            section.add_bar_group(xo=-params.section3.width/2+params.section3.cover, 
                                  yo=0, 
                                  b=params.section3.width - params.section3.cover*2, 
                                  h=0, 
                                  nx=params.section3.mid_bar_nx, 
                                  ny=1, 
                                  area=params.section3.mid_bar_area, 
                                  perimeter_only=True, fiber=fiber_steel)

        section.mesh(rotate = params.section3.rotate)

        # generate PM interaction surface using ACI-318 assumptions
        PM_results = section.run_PM_interaction(fpc=params.section2.fpc1, fy=params.section2.fy, Es=params.section2.Es)

        # plot PM interaction surface
        fig=fkit.plotter.plot_PM(section)

        svg_data = StringIO()
        fig.savefig(svg_data, format='svg')
        plt.close()

        return ImageResult(svg_data)



    def download_mk(self, params, **kwargs):
        # define fibers
        fiber_unconfined = fkit.patchfiber.Todeschini(fpc=params.section2.fpc1)

        fiber_confined   = fkit.patchfiber.Mander(fpc=params.section2.fpc2,
                                                  eo=params.section2.eo, 
                                                  emax=params.section2.emax, 
                                                  default_color="gray")

        fiber_steel      = fkit.nodefiber.Bilinear(fy=params.section2.fy, 
                                                   Es=params.section2.Es)

        # create section
        section = fkit.sectionbuilder.rectangular_confined(width = params.section3.width, 
                                                           height = params.section3.height, 
                                                           cover = params.section3.cover, 
                                                           top_bar = [params.section3.top_bar_area, params.section3.top_bar_nx, 1, 0], 
                                                           bot_bar = [params.section3.bot_bar_area, params.section3.bot_bar_nx, 1, 0], 
                                                           core_fiber = fiber_confined, 
                                                           cover_fiber = fiber_unconfined, 
                                                           steel_fiber = fiber_steel,
                                                           mesh_nx=0.85,
                                                           mesh_ny=0.85)
        if params.section3.mid_bar_area!=0 and params.section3.mid_bar_nx!=0:
            section.add_bar_group(xo=-params.section3.width/2+params.section3.cover, 
                                  yo=0, 
                                  b=params.section3.width - params.section3.cover*2, 
                                  h=0, 
                                  nx=params.section3.mid_bar_nx, 
                                  ny=1, 
                                  area=params.section3.mid_bar_area, 
                                  perimeter_only=True, fiber=fiber_steel)

        section.mesh(rotate = params.section3.rotate)

        # moment-curvature analysis
        MK_results = section.run_moment_curvature(phi_target=params.section4.phi_target, P=params.section4.pu)

        return DownloadResult(MK_results.to_csv(), 'moment_curvature.csv')




    def download_pm(self, params, **kwargs):
        # define fibers
        fiber_unconfined = fkit.patchfiber.Todeschini(fpc=params.section2.fpc1)

        fiber_confined   = fkit.patchfiber.Mander(fpc=params.section2.fpc2,
                                                  eo=params.section2.eo, 
                                                  emax=params.section2.emax, 
                                                  default_color="gray")

        fiber_steel      = fkit.nodefiber.Bilinear(fy=params.section2.fy, 
                                                   Es=params.section2.Es)

        # create section
        section = fkit.sectionbuilder.rectangular_confined(width = params.section3.width, 
                                                           height = params.section3.height, 
                                                           cover = params.section3.cover, 
                                                           top_bar = [params.section3.top_bar_area, params.section3.top_bar_nx, 1, 0], 
                                                           bot_bar = [params.section3.bot_bar_area, params.section3.bot_bar_nx, 1, 0], 
                                                           core_fiber = fiber_confined, 
                                                           cover_fiber = fiber_unconfined, 
                                                           steel_fiber = fiber_steel,
                                                           mesh_nx=0.85,
                                                           mesh_ny=0.85)
        if params.section3.mid_bar_area!=0 and params.section3.mid_bar_nx!=0:
            section.add_bar_group(xo=-params.section3.width/2+params.section3.cover, 
                                  yo=0, 
                                  b=params.section3.width - params.section3.cover*2, 
                                  h=0, 
                                  nx=params.section3.mid_bar_nx, 
                                  ny=1, 
                                  area=params.section3.mid_bar_area, 
                                  perimeter_only=True, fiber=fiber_steel)

        section.mesh(rotate = params.section3.rotate)

        # generate PM interaction surface using ACI-318 assumptions
        PM_results = section.run_PM_interaction(fpc=params.section2.fpc1, fy=params.section2.fy, Es=params.section2.Es)

        return DownloadResult(PM_results.to_csv(), file_name='pm_interaction.csv')