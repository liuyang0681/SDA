import java.awt.Color; 
import java.io.File;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import org.gephi.io.exporter.preview.PNGExporter;
import org.gephi.io.exporter.preview.PDFExporter;
import org.gephi.appearance.plugin.PartitionElementColorTransformer;
import org.gephi.appearance.api.AppearanceController;
import org.gephi.appearance.api.AppearanceModel;
import org.gephi.appearance.api.Ranking;
import org.gephi.appearance.api.*;
import org.gephi.filters.api.FilterController;
import org.gephi.filters.api.Query;
import org.gephi.filters.api.Range;
import org.gephi.filters.plugin.graph.DegreeRangeBuilder.DegreeRangeFilter;
import org.gephi.filters.plugin.graph.EgoBuilder.EgoFilter;
import org.gephi.filters.plugin.operator.INTERSECTIONBuilder.IntersectionOperator;
import org.gephi.filters.plugin.partition.PartitionBuilder.NodePartitionFilter;
import org.gephi.graph.api.DirectedGraph;
import org.gephi.graph.api.UndirectedGraph;
import org.gephi.graph.api.Graph;
import org.gephi.graph.api.GraphController;
import org.gephi.graph.api.GraphModel;
import org.gephi.graph.api.GraphView;
import org.gephi.io.importer.api.Container;
import org.gephi.io.importer.api.ImportController;
import org.gephi.io.processor.plugin.DefaultProcessor;
import org.gephi.project.api.ProjectController;
import org.gephi.project.api.Workspace;
import org.gephi.preview.api.PreviewModel;
import org.gephi.preview.api.PreviewController;
import org.gephi.statistics.plugin.GraphDistance;
import org.gephi.appearance.plugin.UniqueLabelColorTransformer;
import org.gephi.io.exporter.api.ExportController;
import org.gephi.preview.api.PreviewProperty;
import org.gephi.preview.types.EdgeColor;
import org.gephi.graph.api.Node;
import org.gephi.appearance.spi.RankingTransformer;
import org.gephi.graph.api.Column;
import org.gephi.appearance.api.Function;
import org.gephi.appearance.api.Partition;
import org.gephi.appearance.api.PartitionFunction;
import org.gephi.appearance.plugin.PartitionElementColorTransformer;
import org.gephi.appearance.plugin.palette.Palette;
import org.gephi.appearance.plugin.palette.PaletteManager;
import org.gephi.appearance.plugin.RankingElementColorTransformer;
import org.gephi.appearance.plugin.RankingLabelSizeTransformer;
import org.gephi.appearance.plugin.RankingNodeSizeTransformer;
import org.gephi.preview.api.PreviewController;
import org.gephi.preview.api.PreviewModel;
import org.gephi.preview.api.PreviewProperty;
import org.gephi.layout.plugin.fruchterman.FruchtermanReingold;
import org.gephi.layout.plugin.forceAtlas2.ForceAtlas2;
import org.gephi.layout.plugin.force.yifanHu.YifanHuLayout;
import org.gephi.layout.plugin.force.*;
import org.openide.util.Lookup;
import org.gephi.io.exporter.plugin.ExporterGML;



public class Headless
{

    public static void main(String[] args) {
        System.out.println("Hello World!");

         //Init a project - and therefore a workspace
        ProjectController pc = Lookup.getDefault().lookup(ProjectController.class);
        pc.newProject();
        Workspace workspace = pc.getCurrentWorkspace();

        //Get controllers and models
        ImportController importController = Lookup.getDefault().lookup(ImportController.class);
        GraphModel graphModel = Lookup.getDefault().lookup(GraphController.class).getGraphModel();
        PreviewModel model = Lookup.getDefault().lookup(PreviewController.class).getModel();
        FilterController filterController = Lookup.getDefault().lookup(FilterController.class);
        AppearanceController ac = Lookup.getDefault().lookup(AppearanceController.class);
        AppearanceModel am = ac.getModel();
        Graph graph = graphModel.getGraph();

        //Import file
        Container container;
        try {
            File file = new File("mi.cuts.gml");
            container = importController.importFile(file);
        } catch (Exception ex) {
            ex.printStackTrace();
            return;
        }
        //Append imported data to GraphAPI
        importController.process(container, new DefaultProcessor(), workspace);

        //See if graph is well imported
        System.out.println("Nodes: " + graph.getNodeCount());
        System.out.println("Edges: " + graph.getEdgeCount());
        
        /*
        //Filter      
        DegreeRangeFilter degreeFilter = new DegreeRangeFilter();
        degreeFilter.init(graph);
        degreeFilter.setRange(new Range(30, Integer.MAX_VALUE));     //Remove nodes with degree < 30
        Query query = filterController.createQuery(degreeFilter);
        GraphView view = filterController.filter(query);
        graphModel.setVisibleView(view);    //Set the filter result as the visible view
        */
        /*
        //See imports directed and undirected graphs
        UndirectedGraph graphVisible = graphModel.getUndirectedGraphVisible();
        System.out.println("Nodes: " + graphVisible.getNodeCount());
        System.out.println("Edges: " + graphVisible.getEdgeCount());
        //See visible graph stats
        DirectedGraph graphDi = graphModel.getDirectedGraphVisible();
        System.out.println("Nodes: " + graphDi.getNodeCount());
        System.out.println("Edges: " + graphDi.getEdgeCount());
        */ 
        
        
        /*
        //Run YifanHuLayout for 100 passes - The layout always takes the current visible view
        YifanHuLayout layout = new YifanHuLayout(null, new StepDisplacement(1f));
        layout.setGraphModel(graphModel);
        layout.resetPropertiesValues();
        layout.setOptimalDistance(200f);
        layout.initAlgo();
        */
		
		// run FR at low gravity to get well sperated clusters
        ForceAtlas2 layout = new ForceAtlas2(null);
		layout.setGraphModel(graphModel);
        layout.resetPropertiesValues();
        layout.initAlgo();
        System.out.println("Running Layout Algorithum: Force Atlas2");
        for (int i = 0; i < 100*100 && layout.canAlgo(); i++) {
            layout.goAlgo();
        }
        layout.endAlgo();
		// run FR at high gravity to then bring the clusters into a smaller space 
        FruchtermanReingold layout2 = new FruchtermanReingold(null);
        layout2.setGravity(10.01); 
		layout2.setGraphModel(graphModel);
        layout2.resetPropertiesValues();
        layout2.initAlgo();
        System.out.println("Running Layout Algorithum: FruchtermanReingold");
        for (int i = 0; i < 100*100 && layout2.canAlgo(); i++) {
            layout2.goAlgo();
        }
        layout2.endAlgo();





        System.out.println("Done Running Layout Algorithum");


        // add CCID column
        Column ccCol = graphModel.getNodeTable().addColumn("CCID", Integer.class);
        for (Node n : graph.getNodes()) {
            Long d_color = (Long) n.getAttribute("color");
            int i_color = d_color.intValue();
            n.setAttribute(ccCol, i_color);
        }

				int maxPos = 0;
				int minPos = 99999999;
				for (Node n : graph.getNodes()) {
						int pos =  Integer.parseInt((String)n.getAttribute("pos"));

						if (pos > maxPos) {
								maxPos = pos;
						}
						if (pos < minPos) {
								minPos = pos;
						}
				}
				
				
        //List node columns
        for (Column col : graphModel.getNodeTable()) {
            System.out.println(col);
        }

        // colors can be applied to partitions which always come from attribute columns
        Column ccIDColumn = graphModel.getNodeTable().getColumn("CCID");
        //System.out.println(colorColumn);
        Function func = am.getNodeFunction(graph, ccIDColumn, PartitionElementColorTransformer.class);
         if(func != null){
            Partition partition = ((PartitionFunction) func).getPartition();
            Palette palette = PaletteManager.getInstance().generatePalette(partition.size());
            partition.setColors(palette.getColors());
            ac.transform(func);
						for (Node n : graph.getNodes()) {
								int pos =  Integer.parseInt((String)n.getAttribute("pos"));
								float relPos = 0.25f+ 0.75f*((float) (pos - minPos) )/(maxPos-minPos);
								//						n.setAttribute(posCol, relPos);
								
								n.setAlpha(relPos);
						}
        }else{
            System.out.println("Cannot get partition");
            for(Node n : graph.getNodes()){
								int pos =  Integer.parseInt((String)n.getAttribute("pos"));
								float relPos = 0.25f+ 0.75f*((float) (pos - minPos) )/(maxPos-minPos);
								//						n.setAttribute(posCol, relPos);

                n.setColor( Color.BLUE );
								//System.out.println(relPos);
								n.setAlpha(relPos);
            }
        }

				//        Column posCol = graphModel.getNodeTable().addColumn("POS", Double.class);
								
        
        //Size by Degree
        Function degreeRanking = am.getNodeFunction(graph, AppearanceModel.GraphFunction.NODE_DEGREE, RankingNodeSizeTransformer.class);
        RankingNodeSizeTransformer degreeTransformer = (RankingNodeSizeTransformer) degreeRanking.getTransformer();
        degreeTransformer.setMinSize(25);
        degreeTransformer.setMaxSize(40);
        ac.transform(degreeRanking); 
        
        /* 
        //Get Centrality
        GraphDistance distance = new GraphDistance();
        distance.setDirected(true);
        distance.execute(graphModel);
        //Rank size by centrality
        Column centralityColumn = graphModel.getNodeTable().getColumn(GraphDistance.BETWEENNESS);
        Function centralityRanking = am.getNodeFunction(graph, centralityColumn, RankingNodeSizeTransformer.class);
        RankingNodeSizeTransformer centralityTransformer = (RankingNodeSizeTransformer) centralityRanking.getTransformer();
        centralityTransformer.setMinSize(20);
        centralityTransformer.setMaxSize(50);
        ac.transform(centralityRanking);
        */

        // change the node labels 
        for(Node n : graph.getNodes()) {
            int i_color = (Integer) n.getAttribute("CCID");
            String s_color = Integer.toString(i_color);
            n.setLabel( s_color  );
        }

        //Rank label size - set a multiplier size
        /* does not seem to work for me
        Function centralityRanking2 = am.getNodeFunction(graph, centralityColumn, RankingLabelSizeTransformer.class);
        RankingLabelSizeTransformer labelSizeTransformer = (RankingLabelSizeTransformer) centralityRanking2.getTransformer();
        labelSizeTransformer.setMinSize(5);
        labelSizeTransformer.setMaxSize(20);
        ac.transform(centralityRanking2);
        */

        //Preview
        PreviewModel previewModel = Lookup.getDefault().lookup(PreviewController.class).getModel();
        previewModel.getProperties().putValue(PreviewProperty.SHOW_NODE_LABELS, Boolean.TRUE);
        //previewModel.getProperties().putValue(PreviewProperty.NODE_LABEL_PROPORTIONAL_SIZE, Boolean.FALSE);
        model.getProperties().putValue(PreviewProperty.NODE_LABEL_FONT, model.getProperties().getFontValue(PreviewProperty.NODE_LABEL_FONT).deriveFont(8));

        model.getProperties().putValue(PreviewProperty.EDGE_COLOR, new EdgeColor(Color.GRAY));
        model.getProperties().putValue(PreviewProperty.EDGE_THICKNESS, new Float(0.01f));
        // for some reaosn the next line make it so it takes longer of the pdf to laod in default ubunut 
        // but it does not really change the files ize
        model.getProperties().putValue(PreviewProperty.EDGE_OPACITY, new Float(50) );
        model.getProperties().putValue(PreviewProperty.NODE_PER_NODE_OPACITY, true );				
        
        
        //Export
	
        ExportController ec = Lookup.getDefault().lookup(ExportController.class);
				try {
            ec.exportFile(new File("mi.cuts.gml.pdf"));
            System.out.println("Export Happened");
						
        } catch (IOException ex) {
            ex.printStackTrace();
            return;
				}
				/*				
        PDFExporter pdfExporter = (PDFExporter) ec.getExporter("pdf");
				try {
						java.io.FileOutputStream pdfos = new java.io.FileOutputStream("mi.cuts.gml.pdf");
						pdfExporter.setOutputStream(pdfos);
						pdfExporter.execute();				
				}
				catch (java.io.FileNotFoundException e) {
				}
				//Export full graph, save it to test.png and show it in an image frame
        //ec.exportFile(new File("mi.cuts.gml.png"));
        PNGExporter exporter = (PNGExporter) ec.getExporter("png");
				try {
						java.io.FileOutputStream fos = new java.io.FileOutputStream("mi.cuts.gml.png");
						exporter.setOutputStream(fos);
						exporter.execute();
				}
				catch (java.io.FileNotFoundException e) {
				}
				*/
				//        ec.exportStream(baos, exporter);
				//        byte[] png = baos.toByteArray();

				//        pdfExporter.setPageSize(PageSize.A0);
				//        ByteArrayOutputStream baos = new ByteArrayOutputStream();
				//        ec.exportStream(baos, pdfExporter);
				
        //Export
        /*
        ExportController ec2 = Lookup.getDefault().lookup(ExportController.class);
        try {
            ec2.exportFile(new File("mi.cuts.gml.jpg"));
            System.out.println("Export Happened");
        } catch (IOException ex2) {
            ex2.printStackTrace();
            return;
        }*/
        /*
        //PDF Exporter config and export to Byte array
        PDFExporter pdfExporter = (PDFExporter) ec.getExporter("pdf");
        pdfExporter.setPageSize(PageSize.A0);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ec.exportStream(baos, pdfExporter);
        byte[] pdf = baos.toByteArray();
        */
    
	ExportController ec2 = Lookup.getDefault().lookup(ExportController.class);
	ExporterGML gml = (ExporterGML) ec2.getExporter(".gml");

	try {
		ec2.exportFile(new File("cc.positions.gml"), gml);
	} catch (IOException ex) {
		ex.printStackTrace();
	}


	}

}



